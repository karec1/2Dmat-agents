from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Модель пользователя"""
    __tablename__ = 'user'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    full_name = db.Column(db.String(120))
    affiliation = db.Column(db.String(200))
    orcid = db.Column(db.String(19))
    profile_picture = db.Column(db.String(300))  # Add this line
    role = db.Column(db.String(20), default='user')  # user, expert, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Связи
    #materials = db.relationship('Material', backref='author', lazy='dynamic')
    materials = db.relationship('Material', foreign_keys='[Material.user_id]', backref='author', lazy='dynamic')
    verifications = db.relationship('Verification', backref='expert', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_expert(self):
        return self.role in ['expert', 'admin']
    
    def is_admin(self):
        return self.role == 'admin'


class Material(db.Model):
    """Модель для хранения данных о 2D материалах"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Основная информация
    name = db.Column(db.String(200), nullable=False)
    formula = db.Column(db.String(50), nullable=False)
    iupac_name = db.Column(db.String(300))
    cas_number = db.Column(db.String(50))
    
    # Структурные свойства
    crystal_system = db.Column(db.String(50))  # hexagonal, trigonal, etc.
    space_group = db.Column(db.String(20))
    lattice_params = db.Column(db.Text)  # JSON: a, b, c, alpha, beta, gamma
    wyckoff_positions = db.Column(db.Text)  # JSON с позициями атомов
    
    # Вычислительные параметры
    calculation_method = db.Column(db.String(50))  # DFT, DFT+U, HSE, GW
    functional = db.Column(db.String(50))  # PBE, SCAN, HSE06, B3LYP
    software = db.Column(db.String(50))  # VASP, Quantum ESPRESSO, Abinit
    pseudopotential = db.Column(db.String(50))  # PAW, USPP, norm-conserving
    kpoints = db.Column(db.String(100))  # Сетка k-точек
    cut_off_energy = db.Column(db.Float)  # eV
    convergence_criteria = db.Column(db.Text)  # JSON с критериями сходимости
    
    # Электронные свойства
    band_gap = db.Column(db.Float)  # eV
    band_gap_type = db.Column(db.String(10))  # direct/indirect
    fermi_energy = db.Column(db.Float)  # eV
    work_function = db.Column(db.Float)  # eV
    dielectric_constants = db.Column(db.Text)  # JSON: eps_xx, eps_yy, eps_zz
    
    # Магнитные свойства
    magnetic_order = db.Column(db.String(20))  # FM, AFM, ferrimagnetic, spin-glass
    magnetic_moment = db.Column(db.Float)  # μB per unit cell
    easy_axis = db.Column(db.String(20))  # in-plane, out-of-plane
    anisotropy_energy = db.Column(db.Float)  # meV
    curie_temperature = db.Column(db.Float)  # K (расчетная Tc)
    neel_temperature = db.Column(db.Float)  # K (расчетная Tn)
    
    # Обменные параметры
    j1 = db.Column(db.Float)  # ближайшие соседи, meV
    j2 = db.Column(db.Float)  # следующие соседи
    j3 = db.Column(db.Float)
    dmi_constant = db.Column(db.Float)  # meV
    anisotropy_type = db.Column(db.String(20))  # Ising, Heisenberg, XY
    
    # Механические свойства
    formation_energy = db.Column(db.Float)  # eV/atom
    exfoliation_energy = db.Column(db.Float)  # meV/Å²
    elastic_constants = db.Column(db.Text)  # JSON с тензором упругости
    poisson_ratio = db.Column(db.Float)
    young_modulus = db.Column(db.Float)  # GPa
    
    # Термодинамические свойства
    debye_temperature = db.Column(db.Float)  # K
    heat_capacity = db.Column(db.Float)  # J/mol·K
    thermal_conductivity = db.Column(db.Float)  # W/m·K
    
    # Оптические свойства
    refractive_index = db.Column(db.Float)
    absorption_coefficient = db.Column(db.Float)  # cm⁻¹
    photoluminescence = db.Column(db.Float)  # eV
    
    # Файлы и пути
    cif_file_path = db.Column(db.String(300))
    poscar_file_path = db.Column(db.String(300))
    input_files_path = db.Column(db.String(300))  # Папка с входными файлами
    output_files_path = db.Column(db.String(300))  # Папка с выходными файлами
    band_structure_data = db.Column(db.Text)  # JSON с данными зонной структуры
    dos_data = db.Column(db.Text)  # JSON с данными DOS
    charge_density_path = db.Column(db.String(300))
    
    # Метаданные и верификация
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doi = db.Column(db.String(100))
    reference = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    verification_score = db.Column(db.Float)  # 0-100%
    verification_notes = db.Column(db.Text)
    verification_date = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Статистика
    views = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    citations = db.Column(db.Integer, default=0)
    
    # Теги и категории
    tags = db.Column(db.Text)  # JSON список тегов
    applications = db.Column(db.Text)  # JSON список применений
    
    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    
    # Визуализация
    structure_image_path = db.Column(db.String(300))
    reciprocal_lattice_image_path = db.Column(db.String(300))
    band_structure_image_path = db.Column(db.String(300))
    dos_image_path = db.Column(db.String(300))
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'name': self.name,
            'formula': self.formula,
            'crystal_system': self.crystal_system,
            'space_group': self.space_group,
            'band_gap': self.band_gap,
            'magnetic_order': self.magnetic_order,
            'curie_temperature': self.curie_temperature,
            'is_verified': self.is_verified,
            'verification_score': self.verification_score,
            'doi': self.doi,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Verification(db.Model):
    """Модель для верификации материалов экспертами"""
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    expert_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Критерии оценки
    calculation_methodology_score = db.Column(db.Integer)  # 1-5
    data_consistency_score = db.Column(db.Integer)  # 1-5
    reproducibility_score = db.Column(db.Integer)  # 1-5
    documentation_score = db.Column(db.Integer)  # 1-5
    overall_score = db.Column(db.Float)  # среднее
    
    # Детали
    methodology_notes = db.Column(db.Text)
    data_quality_notes = db.Column(db.Text)
    suggested_improvements = db.Column(db.Text)
    is_approved = db.Column(db.Boolean)
    
    # Файлы проверки
    verification_report_path = db.Column(db.String(300))
    
    # Даты
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    material = db.relationship('Material', backref='verification_records')
    
class Comment(db.Model):
    """Комментарии к материалам"""

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # для ответов
    content = db.Column(db.Text, nullable=False)
    is_technical = db.Column(db.Boolean, default=False)  # технический вопрос
    rating = db.Column(db.Integer)  # 1-5 звезд
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    material = db.relationship('Material', backref='comments')
    user = db.relationship('User', backref='comments')
    parent = db.relationship('Comment', remote_side=[id], backref='replies')

class Bookmark(db.Model):
    """Закладки пользователей"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    material = db.relationship('Material', backref='bookmarks')
    user = db.relationship('User', backref='bookmarks')
    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='unique_bookmark'),)
