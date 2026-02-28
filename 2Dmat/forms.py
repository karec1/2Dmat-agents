# forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, SelectField
from wtforms import FloatField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional
from wtforms.fields import DateField, DateTimeField
import re

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', 
                          validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    full_name = StringField('Полное имя', 
                           validators=[DataRequired(), Length(min=2, max=120)])
    affiliation = StringField('Организация', 
                             validators=[DataRequired(), Length(min=2, max=200)])
    orcid = StringField('ORCID ID', 
                       validators=[Optional(), Length(min=16, max=19)])
    password = PasswordField('Пароль', 
                            validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Подтвердите пароль', 
                                    validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_orcid(self, field):
        if field.data:
            # Проверка формата ORCID
            pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
            if not re.match(pattern, field.data):
                raise ValidationError('Неверный формат ORCID ID')


class EditProfileForm(FlaskForm):
    """Форма для редактирования профиля"""
    full_name = StringField('Полное имя', 
                           validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    affiliation = StringField('Организация', 
                             validators=[DataRequired(), Length(min=2, max=200)])
    orcid = StringField('ORCID ID', 
                       validators=[Optional(), Length(min=16, max=19)])
    profile_picture = FileField('Фотография профиля',
                               validators=[Optional(),
                                         FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 
                                                    'Только изображения')])
    submit = SubmitField('Сохранить изменения')
    
    def validate_orcid(self, field):
        if field.data:
            pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
            if not re.match(pattern, field.data):
                raise ValidationError('Неверный формат ORCID ID')


class ChangePasswordForm(FlaskForm):
    """Форма для изменения пароля"""
    current_password = PasswordField('Текущий пароль', 
                                    validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', 
                                validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Подтвердите новый пароль', 
                                    validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Изменить пароль')


class MaterialForm(FlaskForm):
    """Форма для добавления материала"""
    # Основная информация
    name = StringField('Название материала', 
                      validators=[DataRequired(), Length(max=200)])
    formula = StringField('Химическая формула', 
                         validators=[DataRequired(), Length(max=50)])
    iupac_name = StringField('Название по IUPAC', 
                            validators=[Optional(), Length(max=300)])
    cas_number = StringField('CAS номер', 
                           validators=[Optional(), Length(max=50)])
    
    # Структурные свойства
    crystal_system = SelectField('Кристаллическая система',
                               choices=[('', 'Выберите...'),
                                       ('triclinic', 'Триклинная'),
                                       ('monoclinic', 'Моноклинная'),
                                       ('orthorhombic', 'Ромбическая'),
                                       ('tetragonal', 'Тетрагональная'),
                                       ('trigonal', 'Тригональная'),
                                       ('hexagonal', 'Гексагональная'),
                                       ('cubic', 'Кубическая')])
    space_group = StringField('Пространственная группа', 
                             validators=[Optional(), Length(max=20)])
    
    # Вычислительные параметры
    calculation_method = SelectField('Метод расчета',
                                    choices=[('', 'Выберите...'),
                                            ('DFT', 'DFT'),
                                            ('DFT+U', 'DFT+U'),
                                            ('HSE', 'HSE'),
                                            ('GW', 'GW'),
                                            ('MP2', 'MP2'),
                                            ('CCSD', 'CCSD')])
    functional = StringField('Функционал', 
                           validators=[Optional(), Length(max=50)])
    software = StringField('Программное обеспечение', 
                          validators=[Optional(), Length(max=50)])
    
    # Электронные свойства
    band_gap = FloatField('Ширина запрещенной зоны (эВ)', 
                         validators=[Optional()])
    band_gap_type = SelectField('Тип запрещенной зоны',
                               choices=[('', 'Выберите...'),
                                       ('direct', 'Прямая'),
                                       ('indirect', 'Непрямая')])
    
    # Магнитные свойства
    magnetic_order = SelectField('Магнитный порядок',
                                choices=[('', 'Выберите...'),
                                        ('FM', 'Ферромагнетик'),
                                        ('AFM', 'Антиферромагнетик'),
                                        ('ferrimagnetic', 'Ферримагнетик'),
                                        ('spin-glass', 'Спиновое стекло'),
                                        ('paramagnetic', 'Парамагнетик')])
    magnetic_moment = FloatField('Магнитный момент (μB)', 
                                validators=[Optional()])
    curie_temperature = FloatField('Температура Кюри (K)', 
                                  validators=[Optional()])
    
    # Файлы
    cif_file = FileField('Файл CIF', 
                        validators=[FileAllowed(['cif', 'CIF'], 'Только файлы .cif')])
    poscar_file = FileField('Файл POSCAR', 
                           validators=[FileAllowed(['vasp', 'POSCAR'], 'Только файлы VASP')])
    band_structure_file = FileField('Данные зонной структуры (CSV/JSON)', 
                                   validators=[Optional(), 
                                             FileAllowed(['csv', 'json', 'txt'], 
                                                        'Только CSV/JSON/TXT')])
    dos_file = FileField('Данные плотности состояний (CSV/JSON)', 
                        validators=[Optional(), 
                                  FileAllowed(['csv', 'json', 'txt'], 
                                             'Только CSV/JSON/TXT')])
    
    # Метаданные
    doi = StringField('DOI публикации', 
                     validators=[Optional(), Length(max=100)])
    reference = TextAreaField('Ссылка на публикацию', 
                             validators=[Optional()])
    
    # Теги
    tags = StringField('Теги (через запятую)', 
                      validators=[Optional()])
    
    submit = SubmitField('Добавить материал')


class VerificationForm(FlaskForm):
    """Форма для верификации материала"""
    calculation_methodology_score = IntegerField(
        'Методология расчетов (1-5)',
        validators=[DataRequired()]
    )
    data_consistency_score = IntegerField(
        'Согласованность данных (1-5)',
        validators=[DataRequired()]
    )
    reproducibility_score = IntegerField(
        'Воспроизводимость (1-5)',
        validators=[DataRequired()]
    )
    documentation_score = IntegerField(
        'Документация (1-5)',
        validators=[DataRequired()]
    )
    
    methodology_notes = TextAreaField('Замечания по методологии')
    data_quality_notes = TextAreaField('Замечания по качеству данных')
    suggested_improvements = TextAreaField('Предложения по улучшению')
    
    is_approved = BooleanField('Одобрить материал')
    
    verification_report = FileField('Отчет о проверке (PDF)',
                                  validators=[Optional(),
                                            FileAllowed(['pdf'], 'Только PDF')])
    
    submit = SubmitField('Отправить верификацию')


class CommentForm(FlaskForm):
    """Форма для комментариев"""
    content = TextAreaField('Комментарий', 
                           validators=[DataRequired(), Length(min=10, max=1000)])
    is_technical = BooleanField('Технический вопрос')
    rating = SelectField('Оценка',
                        choices=[(0, 'Без оценки'),
                                (1, '1 - Плохо'),
                                (2, '2 - Удовлетворительно'),
                                (3, '3 - Хорошо'),
                                (4, '4 - Очень хорошо'),
                                (5, '5 - Отлично')],
                        coerce=int,
                        default=0)
    submit = SubmitField('Добавить комментарий')