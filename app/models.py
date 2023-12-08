import time
from app import app, db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column(db.Integer, index=True, unique=True)
    last_seen = db.Column(db.Integer, default=round(time.time()))
    secret_word_hash = db.Column(db.String(128))
    location_of_notifications = db.relationship('location_of_notifications_at_the_user', uselist=False)
    access = db.relationship('access_rights_for_users', uselist=False)
    access_panel = db.relationship('user_access_rights_in_the_panel', uselist=False)
    groups = db.relationship('list_of_user_groups')

    def __repr__(self) -> str:
        return '{}'.format(self.id)

    def set_secret_word(self, word):
        self.secret_word_hash = generate_password_hash(word)

    def check_secret_word(self, word):
        return check_password_hash(self.secret_word_hash, word)
    
    def checking_access_to_the_panel(self):
        return users_with_access_to_the_panel.query.filter_by(vk_id=self.vk_id, access='Выдан').first()

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class users_with_access_to_the_panel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column(db.Integer, index=True, unique=True)
    access = db.Column(db.String(32), default='Запрошен')

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class location_of_notifications_at_the_user(db.Model):
    """Расположение уведомлений в интерфейсе"""
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(32), default='upper_left_corner')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class list_of_access_rights_for_users(db.Model):
    """Список прав доступов для куратора"""
    id = db.Column(db.Integer, primary_key=True)
    access_name = db.Column(db.String(32))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class access_rights_for_users(db.Model):
    """Права доступа у кураторов"""
    id = db.Column(db.Integer, primary_key=True)
    access_name = db.Column(db.String(32), default='user')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class marathon_groups(db.Model):
    """Список групп марафонов"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    name_group = db.relationship('names_of_marathon_groups', uselist=False)
    name_environment = db.relationship('name_of_environment_variable_of_marathon_groups', uselist=False)
    user_who_added = db.relationship('users_who_have_add_marathon_groups', uselist=False)
    curators_in_group = db.relationship('list_of_user_groups')
    google_table = db.relationship('tables_linked_to_marathon_groups', uselist=False)
    settings = db.relationship('marathon_group_settings', uselist=False)
    marathon_members = db.relationship('marathon_users')
    posts = db.relationship('posts_in_groups')
    callback_server = db.relationship('group_server_callback_api_data', uselist=False)
    
    def __repr__(self) -> str:
        return '{}'.format(self.id)

class group_server_callback_api_data(db.Model):
    """Данные callback api сервера групп"""
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer)
    url = db.Column(db.String(128))
    title = db.Column(db.String(14))
    secret_key = db.Column(db.String(50))
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class list_of_user_groups(db.Model):
    """Группы в которых состоят кураторы"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class access_rights_for_curators_in_groups(db.Model):
    """Доступы у кураторов по группам"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    access_id = db.Column(db.Integer, db.ForeignKey('list_of_access_rights_for_users.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class marathon_users(db.Model):
    """Обычные пользователи учавствующие в марафоне"""
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column(db.Integer, index=True, unique=True)
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    tasks = db.relationship('status_of_marathon_users_tasks')

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class status_of_marathon_users_tasks(db.Model):
    """Статус ДЗ у пользователей на марафоне"""
    id = db.Column(db.Integer, primary_key=True)
    task_number = db.Column(db.Integer, index=True)
    task_status = db.Column(db.String(16), default='В процессе')
    user_id = db.Column(db.Integer, db.ForeignKey('marathon_users.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    info_post = db.relationship('information_about_the_post_with_the_task', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class information_about_the_post_with_the_task(db.Model):
    """Краткая информация про посты в группах марафонов с ДЗ"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, index=True)
    comment_id = db.Column(db.Integer, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('marathon_users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('status_of_marathon_users_tasks.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class panel_access_rights(db.Model):
    """
    Список прав доступа к панели, чем меньше ID primary_key доступа - тем больше у него прав
    """
    id = db.Column(db.Integer, primary_key=True)
    access_name = db.Column(db.String(32), default='user')

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class user_access_rights_in_the_panel(db.Model):
    """Пользователи с правами доступа к панели"""
    id = db.Column(db.Integer, primary_key=True)
    access_id = db.Column(db.Integer, db.ForeignKey('panel_access_rights.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    access = db.relationship('panel_access_rights')

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class names_of_marathon_groups(db.Model):
    """Названия групп марафонов(если вдруг токен группы марафона станет недействительным)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class name_of_environment_variable_of_marathon_groups(db.Model):
    """Название переменной среды окружения, с помощью которой получается токен группы марафона"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class users_who_have_add_marathon_groups(db.Model):
    """Пользователи которые добавляли группы марафонов в базу"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    time_of_addition = db.Column(db.Integer, default=round(time.time()))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class marathon_group_settings(db.Model):
    """Настройки группы марафона"""
    id = db.Column(db.Integer, primary_key=True)
    name_sheet = db.relationship('name_of_the_marathon_group_table_sheet', uselist=False)
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class name_of_the_marathon_group_table_sheet(db.Model):
    """Название Google таблиц, используемые в марафонах"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='')
    setting_id = db.Column(db.Integer, db.ForeignKey('marathon_group_settings.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class google_marathon_tables(db.Model):
    """Google таблицы, используемые в марафонах"""
    id = db.Column(db.Integer, primary_key=True)
    link_to_the_table = db.Column(db.String(512), index=True, unique=True)
    time_of_addition = db.Column(db.Integer, default=round(time.time()))
    column_settings = db.relationship('table_column_settings', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class tables_linked_to_marathon_groups(db.Model):
    """Google таблицы привязанные к группам марафонов"""
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('google_marathon_tables.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    link_table = db.relationship('google_marathon_tables', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class posts_in_groups(db.Model):
    """Список постов в группах марафонов"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('marathon_groups.id'))
    post_id = db.Column(db.Integer)
    comments = db.relationship('comments_under_posts')

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class comments_under_posts(db.Model):
    """Комментарии под постами групп марафонов"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts_in_groups.id'))
    comment_id = db.Column(db.Integer)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class table_column_settings(db.Model):
    """Данные по колонкам, существующих в Google таблицах, которые будут привязываться к группам марафонов"""
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.relationship('user_name_column_in_the_table', uselist=False)
    user_last_name = db.relationship('user_last_name_column_in_the_table', uselist=False)
    user_reference = db.relationship('user_reference_column_in_the_table', uselist=False)
    user_group = db.relationship('user_group_column_in_the_table', uselist=False)
    user_name_cabinet = db.relationship('user_name_cabinet_column_in_the_table', uselist=False)
    headings = db.relationship('headings_column_in_the_table', uselist=False)
    stop_content = db.relationship('stop_content_column_in_the_table', uselist=False)
    ad_text = db.relationship('ad_text_column_in_the_table', uselist=False)
    ad_media = db.relationship('ad_media_column_in_the_table', uselist=False)
    target_audience = db.relationship('target_audience_column_in_the_table', uselist=False)
    request_stop = db.relationship('request_stop_column_in_the_table', uselist=False)
    launch_status = db.relationship('launch_status_column_in_the_table', uselist=False)
    number_of_tasks = db.relationship('number_of_tasks_in_the_marathon_table', uselist=False)
    tasks = db.relationship('tasks_column_in_the_table', uselist=False)
    table_id = db.Column(db.Integer, db.ForeignKey('google_marathon_tables.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class user_name_column_in_the_table(db.Model):
    """
    Статус колонки с именем пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_user_name_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_user_name_column_in_the_table(db.Model):
    """
    Название колонки с именем пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('user_name_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class user_last_name_column_in_the_table(db.Model):
    """
    Статус колонки с фамилией пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_user_last_name_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_user_last_name_column_in_the_table(db.Model):
    """
    Название колонки с фамилией пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('user_last_name_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class user_reference_column_in_the_table(db.Model):
    """
    Статус колонки с ссылкой VK на пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_user_reference_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_user_reference_column_in_the_table(db.Model):
    """
    Название колонки с ссылкой VK на пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('user_reference_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class user_group_column_in_the_table(db.Model):
    """
    Статус колонки с ссылкой на группу пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_user_group_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_user_group_column_in_the_table(db.Model):
    """
    Название колонки с ссылкой на группу пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('user_group_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class user_name_cabinet_column_in_the_table(db.Model):
    """
    Статус колонки с названием рекламного кабинета пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_user_name_cabinet_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_user_name_cabinet_column_in_the_table(db.Model):
    """
    Название колонки с названием рекламного кабинета пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('user_name_cabinet_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class headings_column_in_the_table(db.Model):
    """
    Статус колонки с рубрикой группы пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_headings_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_headings_column_in_the_table(db.Model):
    """
    Название колонки с рубрикой группы пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('headings_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class stop_content_column_in_the_table(db.Model):
    """
    Статус колонки с данными - стоп-контентом рекламы у группы пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_stop_content_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_stop_content_column_in_the_table(db.Model):
    """
    Название колонки с данными - стоп-контентом рекламы у группы пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('stop_content_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class ad_text_column_in_the_table(db.Model):
    """
    Статус колонки с текстом для рекламы группы пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_ad_text_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_ad_text_column_in_the_table(db.Model):
    """
    Название колонки с текстом для рекламы группы пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('ad_text_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class ad_media_column_in_the_table(db.Model):
    """
    Статус колонки с медиа файлами для рекламы группы пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_ad_media_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_ad_media_column_in_the_table(db.Model):
    """
    Название колонки с медиа файлами для рекламы группы пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('ad_media_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class target_audience_column_in_the_table(db.Model):
    """
    Статус колонки с ЦА для рекламы группы пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_target_audience_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_target_audience_column_in_the_table(db.Model):
    """
    Название колонки с ЦА для рекламы группы пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('target_audience_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class request_stop_column_in_the_table(db.Model):
    """
    Статус колонки с просьбой пользователя остановить рекламу, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_request_stop_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_request_stop_column_in_the_table(db.Model):
    """
    Название колонки с просьбой пользователя остановить рекламу, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('request_stop_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class launch_status_column_in_the_table(db.Model):
    """
    Статус колонки со статусом запуска рекламы группы пользователя, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_launch_status_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_launch_status_column_in_the_table(db.Model):
    """
    Название колонки со статусом запуска рекламы группы пользователя, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('launch_status_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class tasks_column_in_the_table(db.Model):
    """
    Статус колонки с заданиями, 
    availability = True - значит колонка есть и её можно найти через регулярку по названию - initial_word, 
    если False - колонки нет и её нельзя найти
    """
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Boolean, default=False)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))
    initial_word = db.relationship('initial_word_tasks_column_in_the_table', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class initial_word_tasks_column_in_the_table(db.Model):
    """
    Название колонок в которых находится статус заданий, 
    word - слово/преложение находящийся в колонке, по которому будет поиск по регулярке
    """
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(128), default='')
    column_id = db.Column(db.Integer, db.ForeignKey('tasks_column_in_the_table.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)

class number_of_tasks_in_the_marathon_table(db.Model):
    """
    Количество колонок с ДЗ
    """
    id = db.Column(db.Integer, primary_key=True)
    number_of_tasks = db.Column(db.Integer, default=0)
    setting_id = db.Column(db.Integer, db.ForeignKey('table_column_settings.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)