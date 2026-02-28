from flask import Flask
from models import db, Material, User  # Added User import
import json
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///2dmaterials.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Загрузка начальных данных, если база пуста
        if Material.query.count() == 0:
            load_initial_data()
    
    return app


def load_initial_data():
    """Загрузка начальных тестовых данных"""
    try:
        # Создаем тестового пользователя если его нет
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(
                username='admin',
                email='admin@example.com',
                full_name='Администратор Системы',
                affiliation='2DMat Database',
                role='admin'
            )
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()
            print("✅ Создан пользователь admin (пароль: admin123)")
        
        sample_materials = [
            Material(
                name="Chromium(III) iodide",
                formula="CrI3",
                crystal_system="Trigonal",  # Исправлено: structure_type → crystal_system
                space_group="R-3",
                calculation_method="DFT+U",
                functional="PBE+U",
                software="VASP",
                band_gap=1.2,
                band_gap_type="direct",
                magnetic_order="FM",
                magnetic_moment=3.0,
                easy_axis="out-of-plane",
                anisotropy_energy=0.7,
                curie_temperature=45.0,  # Исправлено: tc_estimate → curie_temperature
                formation_energy=-0.5,
                exfoliation_energy=25.0,
                j1=-2.5,
                j2=0.3,
                doi="10.1038/nature22391",
                reference="Huang et al., Nature 546, 270 (2017)",
                user_id=user.id,  # Добавлено: связь с пользователем
                is_public=True,  # Добавлено: обязательное поле
                is_verified=True,
                verification_score=95.0
            ),
            Material(
                name="Chromium germanium telluride",
                formula="Cr2Ge2Te6",
                crystal_system="Trigonal",
                space_group="P3m1",
                calculation_method="DFT",
                functional="PBE",
                software="Quantum ESPRESSO",
                band_gap=0.8,
                band_gap_type="indirect",
                magnetic_order="FM",
                magnetic_moment=6.0,
                easy_axis="out-of-plane",
                anisotropy_energy=0.3,
                curie_temperature=61.0,
                formation_energy=-0.7,
                exfoliation_energy=30.0,
                j1=-4.2,
                j2=0.5,
                doi="10.1021/acs.nanolett.7b01349",
                reference="Gong et al., Nature 546, 265 (2017)",
                user_id=user.id,
                is_public=True,
                is_verified=True,
                verification_score=90.0
            ),
            Material(
                name="Iron(III) chloride",
                formula="FeCl3",
                crystal_system="Trigonal",
                space_group="P-3m1",
                calculation_method="DFT",
                functional="HSE06",
                software="VASP",
                band_gap=0.5,
                band_gap_type="direct",
                magnetic_order="AFM",
                magnetic_moment=5.0,
                easy_axis="in-plane",
                anisotropy_energy=0.1,
                curie_temperature=15.0,
                formation_energy=-0.3,
                exfoliation_energy=20.0,
                j1=8.5,
                j2=-1.2,
                doi="10.1103/PhysRevB.98.214420",
                reference="Jiang et al., Phys. Rev. B 98, 214420 (2018)",
                user_id=user.id,
                is_public=True,
                is_verified=False,
                verification_score=75.0
            )
        ]
        
        for material in sample_materials:
            db.session.add(material)
        
        db.session.commit()
        print(f"✅ Загружено {len(sample_materials)} тестовых материалов")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при загрузке данных: {e}")
        import traceback
        traceback.print_exc()