from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
import csv
import io
import secrets

from PIL import Image
from models import db, User, Material, Verification, Comment, Bookmark
from forms import (
    LoginForm, RegistrationForm, MaterialForm, VerificationForm,
    CommentForm, EditProfileForm, ChangePasswordForm
)
from utils.visualization import StructureVisualizer, BandStructureVisualizer, DOSVisualizer
from flask_migrate import Migrate
from translations import translations, get_locale

# Конфигурация
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///2dmaterials.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Создание папок для загрузок
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'cif'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'poscar'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'bands'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'dos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'reports'), exist_ok=True)

# Инициализация
db.init_app(app)
CORS(app)

migrate = Migrate(app, db)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'ru']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))


@app.context_processor
def inject_translations():
    def t(key):
        lang = session.get('language', request.accept_languages.best_match(['en', 'ru']) or 'en')
        return translations.get(lang, translations['en']).get(key, key)
    return dict(t=t)

# Helper function for 404 errors
def get_or_404(model, id):
    result = db.session.get(model, id)
    if result is None:
        abort(404)
    return result

# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user
        if not db.session.query(User).filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@miem.hse.ru',
                full_name='Администратор системы',
                affiliation='НИУ ВШЭ, МИЭМ',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")
    except Exception as e:
        print(f"Error initializing database: {e}")


def save_profile_picture(form_picture):
    """Сохраняет фотографию профиля и возвращает имя файла"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads/profiles', picture_fn)
    
    # Resize image
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Главная страница
@app.route('/')
def index():
    stats = {
        'total_materials': db.session.query(Material).count(),
        'verified_materials': db.session.query(Material).filter_by(is_verified=True).count(),
        'total_users': db.session.query(User).count(),
        'recent_materials': db.session.query(Material).order_by(Material.created_at.desc()).limit(6).all(),
        'top_materials': db.session.query(Material).order_by(Material.views.desc()).limit(6).all(),
        'fm_materials': db.session.query(Material).filter_by(magnetic_order='FM').count(),
        'afm_materials': db.session.query(Material).filter_by(magnetic_order='AFM').count()
    }
    return render_template('index.html', stats=stats)

# Просмотр материалов
@app.route('/browse')
def browse():
    # Получение параметров фильтрации из запроса
    formula = request.args.get('formula', '').strip()
    magnetic_order = request.args.get('magnetic_order', '').strip()
    verified_only = request.args.get('verified_only', 'false') == 'true'
    
    try:
        min_tc = float(request.args.get('min_tc', 0))
    except ValueError:
        min_tc = 0
        
    try:
        max_band_gap = float(request.args.get('max_band_gap', 10))
    except ValueError:
        max_band_gap = 10
    
    # Пагинация
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Start query
    query = db.session.query(Material).filter(Material.is_public == True)
    
    # Apply filters
    if formula:
        query = query.filter(Material.formula.ilike(f'%{formula}%'))
    if magnetic_order:
        query = query.filter_by(magnetic_order=magnetic_order)
    if verified_only:
        query = query.filter_by(is_verified=True)
    if min_tc > 0:
        query = query.filter(Material.curie_temperature >= min_tc)
    if max_band_gap < 10:
        query = query.filter(Material.band_gap <= max_band_gap)
    
    # Get total count
    total = query.count()
    
    # Paginate
    materials = query.order_by(Material.created_at.desc())\
                    .offset((page - 1) * per_page)\
                    .limit(per_page).all()
    
    # Get unique magnetic orders for filter dropdown
    unique_orders = db.session.query(Material.magnetic_order).distinct().filter(
        Material.magnetic_order.isnot(None)
    ).all()
    unique_orders = [order[0] for order in unique_orders]
    
    return render_template('browse.html', 
                         materials=materials,
                         unique_orders=unique_orders,
                         filters={
                             'formula': formula,
                             'magnetic_order': magnetic_order,
                             'verified_only': verified_only,
                             'min_tc': min_tc,
                             'max_band_gap': max_band_gap
                         },
                         pagination={
                             'page': page,
                             'per_page': per_page,
                             'total': total,
                             'pages': (total + per_page - 1) // per_page
                         })

# Детальная страница материала
@app.route('/material/<int:material_id>')
def material_detail(material_id):
    material = get_or_404(Material, material_id)
    if not material:
        abort(404)
    
    # Увеличиваем счетчик просмотров
    material.views += 1
    db.session.commit()
    
    # Загружаем данные для визуализации
    structure_image = None
    band_structure_image = None
    dos_image = None
    
    if material.cif_file_path and os.path.exists(material.cif_file_path):
        structure_image = StructureVisualizer.create_structure_plot(
            material.cif_file_path
        )
    
    if material.band_structure_data:
        try:
            band_data = json.loads(material.band_structure_data)
            band_structure_image = BandStructureVisualizer.create_band_structure_plot(band_data)
        except (json.JSONDecodeError, ValueError):
            pass
    
    if material.dos_data:
        try:
            dos_data = json.loads(material.dos_data)
            dos_image = DOSVisualizer.create_dos_plot(dos_data)
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Комментарии
    comments = Comment.query.filter_by(material_id=material_id).order_by(
        Comment.created_at.desc()
    ).all()
    
    # Проверка, добавлен ли в закладки
    is_bookmarked = False
    if current_user.is_authenticated:
        bookmark = Bookmark.query.filter_by(
            user_id=current_user.id,
            material_id=material_id
        ).first()
        is_bookmarked = bookmark is not None
    
    return render_template('material.html',
                         material=material,
                         structure_image=structure_image,
                         band_structure_image=band_structure_image,
                         dos_image=dos_image,
                         comments=comments,
                         is_bookmarked=is_bookmarked)

# Визуализация
@app.route('/material/<int:material_id>/visualization')
@login_required
def material_visualization(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Интерактивные визуализации
    interactive_structure = None
    interactive_bands = None
    interactive_dos = None
    
    if material.cif_file_path and os.path.exists(material.cif_file_path):
        interactive_structure = StructureVisualizer.create_interactive_structure(
            material.cif_file_path
        )
    
    if material.band_structure_data:
        try:
            band_data = json.loads(material.band_structure_data)
            interactive_bands = BandStructureVisualizer.create_interactive_bands(band_data)
        except (json.JSONDecodeError, ValueError):
            pass
    
    if material.dos_data:
        try:
            dos_data = json.loads(material.dos_data)
            interactive_dos = DOSVisualizer.create_interactive_dos(dos_data)
        except (json.JSONDecodeError, ValueError):
            pass
    
    return render_template('visualization.html',
                         material=material,
                         interactive_structure=interactive_structure,
                         interactive_bands=interactive_bands,
                         interactive_dos=interactive_dos)

# Добавление материала
@app.route('/add_material', methods=['GET', 'POST'])
@login_required
def add_material():
    form = MaterialForm()
    
    if form.validate_on_submit():
        # Сохранение файлов
        cif_filename = None
        poscar_filename = None
        bands_filename = None
        dos_filename = None
        
        if form.cif_file.data:
            cif_filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form.cif_file.data.filename}")
            form.cif_file.data.save(
                os.path.join(app.config['UPLOAD_FOLDER'], 'cif', cif_filename)
            )
        
        if form.poscar_file.data:
            poscar_filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form.poscar_file.data.filename}")
            form.poscar_file.data.save(
                os.path.join(app.config['UPLOAD_FOLDER'], 'poscar', poscar_filename)
            )
        
        # Создание материала
        material = Material(
            name=form.name.data,
            formula=form.formula.data,
            iupac_name=form.iupac_name.data or None,
            cas_number=form.cas_number.data or None,
            crystal_system=form.crystal_system.data or None,
            space_group=form.space_group.data or None,
            calculation_method=form.calculation_method.data or None,
            functional=form.functional.data or None,
            software=form.software.data or None,
            band_gap=form.band_gap.data or None,
            band_gap_type=form.band_gap_type.data or None,
            magnetic_order=form.magnetic_order.data or None,
            magnetic_moment=form.magnetic_moment.data or None,
            curie_temperature=form.curie_temperature.data or None,
            doi=form.doi.data or None,
            reference=form.reference.data or None,
            user_id=current_user.id,
            is_public=True
        )
        
        # Пути к файлам
        if cif_filename:
            material.cif_file_path = os.path.join('static/uploads/cif', cif_filename)
        
        if poscar_filename:
            material.poscar_file_path = os.path.join('static/uploads/poscar', poscar_filename)
        
        # Теги
        if form.tags.data:
            tags_list = [tag.strip() for tag in form.tags.data.split(',')]
            material.tags = json.dumps(tags_list)
        
        db.session.add(material)
        db.session.commit()
        
        flash('Материал успешно добавлен!', 'success')
        return redirect(url_for('material_detail', material_id=material.id))
    
    return render_template('add_material.html', form=form)

# Верификация материала
@app.route('/material/<int:material_id>/verify', methods=['GET', 'POST'])
@login_required
def verify_material(material_id):
    if not current_user.is_expert():
        flash('Только эксперты могут верифицировать материалы.', 'danger')
        return redirect(url_for('material_detail', material_id=material_id))
    
    material = Material.query.get_or_404(material_id)
    form = VerificationForm()
    
    if form.validate_on_submit():
        # Расчет общего балла
        scores = [
            form.calculation_methodology_score.data,
            form.data_consistency_score.data,
            form.reproducibility_score.data,
            form.documentation_score.data
        ]
        overall_score = sum(scores) / len(scores)
        
        # Создание верификации
        verification = Verification(
            material_id=material_id,
            expert_id=current_user.id,
            calculation_methodology_score=form.calculation_methodology_score.data,
            data_consistency_score=form.data_consistency_score.data,
            reproducibility_score=form.reproducibility_score.data,
            documentation_score=form.documentation_score.data,
            overall_score=overall_score,
            methodology_notes=form.methodology_notes.data or None,
            data_quality_notes=form.data_quality_notes.data or None,
            suggested_improvements=form.suggested_improvements.data or None,
            is_approved=form.is_approved.data,
            completed_at=datetime.utcnow()
        )
        
        # Обновление материала
        material.is_verified = form.is_approved.data
        material.verification_score = overall_score * 20  # Перевод в проценты
        material.verification_notes = f"{form.methodology_notes.data or ''}\n{form.data_quality_notes.data or ''}"
        material.verification_date = datetime.utcnow()
        material.verified_by = current_user.id
        
        db.session.add(verification)
        db.session.commit()
        
        flash('Верификация завершена!', 'success')
        return redirect(url_for('material_detail', material_id=material_id))
    
    return render_template('verify_material.html', form=form, material=material)

# Личный кабинет
@app.route('/profile')
@login_required
def profile():
    user_materials = Material.query.filter_by(user_id=current_user.id).all()
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    verifications = Verification.query.filter_by(expert_id=current_user.id).all()
    
    return render_template('profile.html',
                         user=current_user,
                         materials=user_materials,
                         bookmarks=bookmarks,
                         verifications=verifications)


@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
    
    all_materials = Material.query.order_by(Material.created_at.desc()).all()
    all_users = User.query.all()
    pending_materials = Material.query.filter_by(is_verified=False, is_public=True).order_by(Material.created_at.desc()).all()
    
    return render_template('admin.html',
                         materials=all_materials,
                         users=all_users,
                         pending_materials=pending_materials,
                         pending_count=len(pending_materials))


# Добавление комментария
@app.route('/material/<int:material_id>/comment', methods=['POST'])
@login_required
def add_comment(material_id):
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            material_id=material_id,
            user_id=current_user.id,
            content=form.content.data,
            is_technical=form.is_technical.data,
            rating=form.rating.data if form.rating.data != 0 else None
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Комментарий добавлен!', 'success')
    
    return redirect(url_for('material_detail', material_id=material_id))

# Добавление в закладки
@app.route('/material/<int:material_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(material_id):
    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id,
        material_id=material_id
    ).first()
    
    if bookmark:
        db.session.delete(bookmark)
        message = 'Удалено из закладок'
    else:
        bookmark = Bookmark(
            user_id=current_user.id,
            material_id=material_id
        )
        db.session.add(bookmark)
        message = 'Добавлено в закладки'
    
    db.session.commit()
    return jsonify({'success': True, 'message': message})

# API endpoints
@app.route('/api/materials')
def api_materials():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page
    
    query = Material.query.filter_by(is_public=True)
    total = query.count()
    materials = query.offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'materials': [m.to_dict() for m in materials],
        'total': total,
        'pages': pages,
        'current_page': page
    })

@app.route('/api/material/<int:material_id>')
def api_material_detail(material_id):
    material = Material.query.get_or_404(material_id)
    
    if not material.is_public:
        return jsonify({'error': 'Material is not public'}), 403
    
    result = material.to_dict()
    
    # Добавляем детали
    details = {
        'structural': {
            'crystal_system': material.crystal_system,
            'space_group': material.space_group,
            'lattice_params': json.loads(material.lattice_params) if material.lattice_params else None
        },
        'electronic': {
            'band_gap': material.band_gap,
            'band_gap_type': material.band_gap_type,
            'fermi_energy': material.fermi_energy
        },
        'magnetic': {
            'order': material.magnetic_order,
            'moment': material.magnetic_moment,
            'curie_temperature': material.curie_temperature,
            'neel_temperature': material.neel_temperature,
            'anisotropy_energy': material.anisotropy_energy,
            'easy_axis': material.easy_axis
        },
        'verification': {
            'is_verified': material.is_verified,
            'score': material.verification_score,
            'date': material.verification_date.isoformat() if material.verification_date else None
        }
    }
    
    result.update(details)
    return jsonify(result)

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'total_materials': Material.query.count(),
        'fm_materials': Material.query.filter_by(magnetic_order='FM').count(),
        'afm_materials': Material.query.filter_by(magnetic_order='AFM').count(),
        'verified_materials': Material.query.filter_by(is_verified=True).count()
    })

# Аутентификация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Вы успешно вошли в систему!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Пароли не совпадают.', 'danger')
            return render_template('register.html', form=form)
        
        # Проверка существования пользователя
        if User.query.filter_by(username=form.username.data).first():
            flash('Это имя пользователя уже занято.', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Этот email уже используется.', 'danger')
            return render_template('register.html', form=form)
        
        # Создание пользователя
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            affiliation=form.affiliation.data,
            orcid=form.orcid.data or None
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Add edit profile route
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Этот email уже используется другим пользователем.', 'danger')
            return render_template('edit_profile.html', form=form)
        
        # Update user data
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.affiliation = form.affiliation.data
        current_user.orcid = form.orcid.data or None
        
        # Save profile picture if provided
        if form.profile_picture.data:
            picture_file = save_profile_picture(form.profile_picture.data)
            current_user.profile_picture = picture_file
        
        db.session.commit()
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        # Pre-populate form with current data
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
        form.affiliation.data = current_user.affiliation
        form.orcid.data = current_user.orcid
    
    return render_template('edit_profile.html', form=form)

# Add change password route
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()  # We'll create this form
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Неверный текущий пароль.', 'danger')
            return render_template('change_password.html', form=form)
        
        # Check if new passwords match
        if form.new_password.data != form.confirm_password.data:
            flash('Новые пароли не совпадают.', 'danger')
            return render_template('change_password.html', form=form)
        
        # Set new password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Пароль успешно изменен!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('change_password.html', form=form)

# Edit material route
@app.route('/material/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if user owns the material or is admin
    if material.user_id != current_user.id and not current_user.is_admin():
        flash('Вы не можете редактировать этот материал.', 'danger')
        return redirect(url_for('material_detail', material_id=material_id))
    
    form = MaterialForm()
    
    if form.validate_on_submit():
        # Update material data
        material.name = form.name.data
        material.formula = form.formula.data
        material.iupac_name = form.iupac_name.data or None
        material.cas_number = form.cas_number.data or None
        material.crystal_system = form.crystal_system.data or None
        material.space_group = form.space_group.data or None
        material.calculation_method = form.calculation_method.data or None
        material.functional = form.functional.data or None
        material.software = form.software.data or None
        material.band_gap = form.band_gap.data or None
        material.band_gap_type = form.band_gap_type.data or None
        material.magnetic_order = form.magnetic_order.data or None
        material.magnetic_moment = form.magnetic_moment.data or None
        material.curie_temperature = form.curie_temperature.data or None
        material.doi = form.doi.data or None
        material.reference = form.reference.data or None
        
        # Handle file uploads (similar to add_material)
        if form.cif_file.data:
            cif_filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form.cif_file.data.filename}")
            form.cif_file.data.save(
                os.path.join(app.config['UPLOAD_FOLDER'], 'cif', cif_filename)
            )
            material.cif_file_path = os.path.join('static/uploads/cif', cif_filename)
        
        if form.poscar_file.data:
            poscar_filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form.poscar_file.data.filename}")
            form.poscar_file.data.save(
                os.path.join(app.config['UPLOAD_FOLDER'], 'poscar', poscar_filename)
            )
            material.poscar_file_path = os.path.join('static/uploads/poscar', poscar_filename)
        
        # Update tags
        if form.tags.data:
            tags_list = [tag.strip() for tag in form.tags.data.split(',')]
            material.tags = json.dumps(tags_list)
        
        material.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Материал успешно обновлен!', 'success')
        return redirect(url_for('material_detail', material_id=material.id))
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.name.data = material.name
        form.formula.data = material.formula
        form.iupac_name.data = material.iupac_name
        form.cas_number.data = material.cas_number
        form.crystal_system.data = material.crystal_system
        form.space_group.data = material.space_group
        form.calculation_method.data = material.calculation_method
        form.functional.data = material.functional
        form.software.data = material.software
        form.band_gap.data = material.band_gap
        form.band_gap_type.data = material.band_gap_type
        form.magnetic_order.data = material.magnetic_order
        form.magnetic_moment.data = material.magnetic_moment
        form.curie_temperature.data = material.curie_temperature
        form.doi.data = material.doi
        form.reference.data = material.reference
        
        if material.tags:
            tags_list = json.loads(material.tags)
            form.tags.data = ', '.join(tags_list)
    
    return render_template('edit_material.html', form=form, material=material)

# Delete material route
@app.route('/material/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if user owns the material or is admin
    if material.user_id != current_user.id and not current_user.is_admin():
        flash('Вы не можете удалить этот материал.', 'danger')
        return redirect(url_for('material_detail', material_id=material_id))
    
    db.session.delete(material)
    db.session.commit()
    
    flash('Материал успешно удален!', 'success')
    return redirect(url_for('profile'))

# Экспорт данных
@app.route('/export/csv')
def export_csv():
    materials = Material.query.filter_by(is_public=True).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID', 'Formula', 'Name', 'Crystal System', 'Space Group',
        'Band Gap (eV)', 'Band Gap Type', 'Magnetic Order',
        'Magnetic Moment (μB)', 'Curie Temperature (K)',
        'Is Verified', 'Verification Score (%)', 'DOI', 'Created At'
    ])
    
    # Данные
    for m in materials:
        writer.writerow([
            m.id,
            m.formula,
            m.name or '',
            m.crystal_system or '',
            m.space_group or '',
            f"{m.band_gap:.3f}" if m.band_gap is not None else '',
            m.band_gap_type or '',
            m.magnetic_order or '',
            f"{m.magnetic_moment:.2f}" if m.magnetic_moment is not None else '',
            f"{m.curie_temperature:.1f}" if m.curie_temperature is not None else '',
            'Yes' if m.is_verified else 'No',
            f"{m.verification_score:.1f}" if m.verification_score is not None else '',
            m.doi or '',
            m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else ''
        ])
    
    output.seek(0)
    csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name='2d_materials_database.csv'
    )


@app.route('/admin/backup')
@login_required
def backup_database():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    import shutil
    from datetime import datetime
    
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    backup_dir = os.path.join(app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'backup_{timestamp}.db')
    
    try:
        shutil.copy2(db_path, backup_path)
        flash(f'Backup created: backup_{timestamp}.db', 'success')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/restore/<filename>')
@login_required
def restore_database(filename):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    import shutil
    from datetime import datetime
    
    backup_dir = os.path.join(app.root_path, 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_path):
        flash('Backup file not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore = db_path + f'.pre_restore_{timestamp}'
        shutil.copy2(db_path, pre_restore)
        
        shutil.copy2(backup_path, db_path)
        flash(f'Database restored from {filename}', 'success')
    except Exception as e:
        flash(f'Restore failed: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/backups')
@login_required
def list_backups():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    backup_dir = os.path.join(app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backups = []
    if os.path.exists(backup_dir):
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith('.db'):
                filepath = os.path.join(backup_dir, f)
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                backups.append({
                    'name': f,
                    'size': size,
                    'mtime': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('backups.html', backups=backups)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
