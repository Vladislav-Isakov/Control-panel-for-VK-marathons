from datetime import datetime
import random
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from flask import render_template, flash, redirect, url_for, request, \
    jsonify, make_response, get_flashed_messages, abort, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db, csfr
from app.models import User, marathon_groups, users_with_access_to_the_panel
from app.functions import loading_list_of_curator_groups, granting_rights_in_the_panel, revocation_of_rights_in_the_panel, check_user_in_database, loading_list_of_users_with_rights, \
    add_marathon_group, loading_list_of_marathon_groups, delete_marathon_group, loading_list_curators_in_marathon_groups, removing_curator_from_marathon_group, transfer_of_the_curator_from_group_to_group, \
    adding_google_tables, list_of_google_tables, delete_google_tables, linking_table_to_marathon_group, loading_curator_group_data, loading_post_comments, loading_group_table_settings, loading_list_post_comment_thread, \
    sending_the_curator_response_to_comment, values_update_in_google_spreadsheet, edit_status_of_user_task, loading_marathon_group_settings, edit_marathon_group_settings, loading_list_of_curators_to_add_to_group, \
    add_curator_to_group, loading_list_of_user_tasks_by_category, granting_the_user_access_to_the_panel, removing_user_access_to_the_panel, list_users_with_access_to_the_panel, edit_callback_server_settings_in_group, \
    event_handling_new_post
from app.forms import LoginForm
import requests
from requests.exceptions import Timeout
import time
import os
import hashlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@app.before_request
async def before_request():
    if current_user.is_authenticated:
        if current_user.checking_access_to_the_panel() is None:
            flash('У Вас нет доступа к панели управления, вы будете разлогинены.', 'info')
            logout_user()
        current_user.last_seen = round(time.time())
        db.session.commit()

@app.route('/api/vk/callback_api/<int:group_id>', methods=['POST'])
@csfr.exempt
async def api_vk_callback_api(group_id):
    """URL принимающий события в группах от сервера Callback Api VK"""
    if request.json.get('type', None) is not None:
        if request.json.get('type', None) == 'confirmation':
            name_environment_group = f'group_{request.json.get("group_id")}'
            if os.environ.get(name_environment_group, None) is None:
                return 'ok'
            try:
                confirmation_callback_api_vk = requests.post('https://api.vk.com/method/groups.getCallbackConfirmationCode?access_token={}&v=5.131'.format(os.environ.get(name_environment_group)), data={'group_id': int(group_id)}, timeout=10).json()['response']
            except Timeout:
                return 'ok'
            except KeyError:
                return 'ok'
            await edit_callback_server_settings_in_group(int(group_id))
            return str(confirmation_callback_api_vk['code'])
        elif request.json.get('type', None) == 'wall_post_new':
            await event_handling_new_post(int(group_id), request.json)
    return 'ok'

@app.route('/', methods=['GET', 'POST'])
@login_required
async def index():
    """Домашняя - главная страница панели управления марафонами"""
    
    list_groups = await loading_list_of_curator_groups()
    list_tables = await list_of_google_tables()

    response = make_response(render_template('groups_list.html', list_groups=list_groups, list_tables=list_tables))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/google')
@login_required
def google():
    """
    URL отвечает за проверку и генерацию доступа к общей Google таблицы
    Если доступа нет, перенаправляет на генерацию доступа
    Если срок действия доступа истёк, и выводит ошибку, необходимо удалить файл token.json в главном каталоге проекта
    """
    SCOPES = app.config['SCOPES_GOOGLE']
    SAMPLE_SPREADSHEET_ID = '' #ID главной Google таблицы марафонов
    SAMPLE_RANGE_NAME = 'A1:B2'
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            flow.authorization_url(access_type='offline')
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
    except HttpError as err:
        ...
    return 'Ok'

@app.get('/group')
@login_required
async def show_group_get():
    """Данные по конкретной группе VK марафона"""
    if request.args.get('group_id', None) is None or str(request.args.get('group_id')) == '':
        return redirect(url_for('index'))
    group_data = await loading_curator_group_data(int(request.args.get('group_id')))
    #Установка заголовков ответа сервера
    response = make_response(render_template('show_group.html', group_data=group_data))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/users_with_rights')
@login_required
async def users_with_rights():
    """Список пользователей с выданными правами в панели"""
    list_users = await loading_list_of_users_with_rights()
    #Установка заголовков ответа сервера
    response = make_response(render_template('list_users_with_rights.html', list_users=list_users))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/curator_groups')
@login_required
async def curator_groups():
    """Список групп марафонов, за которыми закреплён конкретный куратор"""
    list_groups = await loading_list_of_curator_groups()
    #Установка заголовков ответа сервера
    response = make_response(render_template('list_curator_groups.html', list_groups=list_groups))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/post_comments')
@login_required
async def post_comments():
    """Список комментариев под постом, без веток(вложенных) комментариев"""
    if request.args.get('group_id', None) is None:
        flash('Произошла ошибка при загрузке комментариев, не найдено значение номера группы.', 'error')
        return ''
    elif request.args.get('post_id', None) is None:
        flash('Произошла ошибка при загрузке комментариев, не найдено значение номера поста.', 'error')
        return ''
    elif request.args.get('page', None) is None:
        flash('Произошла ошибка при загрузке комментариев, не найдено значение номера страницы.', 'error')
        return ''
    
    list_comments = await loading_post_comments(int(request.args.get('group_id')), int(request.args.get('post_id')), int(request.args.get('page')))
    table_settings = await loading_group_table_settings(int(request.args.get('group_id')))

    #Установка заголовков ответа сервера
    response = make_response(render_template('list_comments_under_the_post.html', list_comments=list_comments, table_settings=table_settings))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/post_comment_thread')
@login_required
async def post_comment_thread():
    """Запрос ветки комментариев(вложенных) у конкретного комментария"""
    if request.args.get('group_id', None) is None:
        flash('Произошла ошибка при загрузке ветки комментария, не найдено значение номера группы.', 'error')
        return ''
    elif request.args.get('post_id', None) is None:
        flash('Произошла ошибка при загрузке ветки комментария, не найдено значение номера поста.', 'error')
        return ''
    elif request.args.get('comment_id', None) is None:
        flash('Произошла ошибка при загрузке ветки комментария, не найдено значение номера комментария.', 'error')
        return ''
    
    list_comment_thread = await loading_list_post_comment_thread(int(request.args.get('group_id')), int(request.args.get('post_id')), int(request.args.get('comment_id')))
    table_settings = await loading_group_table_settings(int(request.args.get('group_id')))

    response = make_response(render_template('list_comment_thread.html', list_comments=list_comment_thread, table_settings=table_settings))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.post('/response_to_comment')
@login_required
async def response_to_comment():
    """Система ответа на комментарий пользователя из панели"""
    if request.form.get('group_id', None) is None or request.form.get('post_id', None) is None or request.form.get('comment_id', None) is None:
        flash('Неудалось отправить комментарий, не найдено значение группы/поста/комментария, перезагрузите страницу и повторите попытку.', 'error')
        return redirect('/', 303)
    elif request.form.get('comment_text', None) is None or str(request.form.get('comment_text', '')) == '' and request.files.get('comment_attachments', None) is None or request.files.getlist('comment_attachments') == []:
        flash('Неудалось отправить комментарий т.к Вы не написали комментарий/прикрепили вложения.', 'error')
        return redirect('/', 303)
    await sending_the_curator_response_to_comment(int(request.form.get('group_id')), int(request.form.get('post_id')), int(request.form.get('comment_id')))
    return redirect('/', 303)

@app.post('/edit_cell_value')
@login_required
async def edit_cell_value():
    """Изменение ячейки Goggle таблицы, изменять можно в графическом интерфейсе"""
    info_group = db.session.query(marathon_groups).filter(marathon_groups.id == request.form.get('group_id')).options(joinedload(marathon_groups.google_table)).first()
    if info_group is None:
        flash('Произошла ошибка изменения ячейки, не обнаружен ID группы.', 'error')
        return redirect('/', 303)
    elif request.form.get('cell', None) is None:
        flash('Произошла ошибка изменения ячейки, не обнаружены координаты ячейки.', 'error')
        return redirect('/', 303)
    elif request.form.get('value', None) is None:
        flash('Произошла ошибка изменения ячейки, не обнаружено изменённое значение ячейки.', 'error')
        return redirect('/', 303)
    await values_update_in_google_spreadsheet(str(info_group.google_table.link_table.link_to_the_table), f"{request.form.get('page')}!{request.form.get('cell')}", str(request.form.get('value')))
    return redirect('/', 303)

@app.post('/edit_task_status')
@login_required
async def edit_task_status():
    """
    Изменение статуса ДЗ пользователя
    group_id - число
    user_id - число
    task_status - строка статуса, на который нужно изменить (Сделано, В процессе), иные статусы будут отклоняться.
    post_id - число ID поста с ДЗ в группе VK
    comment_id - число комментария пользователя, по которому будет идти поиск его ДЗ и статуса ДЗ
    """
    if request.form.get('group_id', None) is None:
        flash('Ошибка изменения статуса задания, не обнаружен ID группы.', 'error')
        return redirect('/', 303)
    elif request.form.get('user_id', None) is None:
        flash('Ошибка изменения статуса задания, не обнаружен ID пользователя.', 'error')
        return redirect('/', 303)
    elif request.form.get('task_number', None) is None:
        flash('Ошибка изменения статуса задания, не обнаружен номер задания.', 'error')
        return redirect('/', 303)
    elif request.form.get('task_status', None) is None:
        flash('Ошибка изменения статуса задания, не обнаружен статус задания.', 'error')
        return redirect('/', 303)
    elif request.form.get('post_id', None) is None:
        flash('Ошибка изменения статуса задания, не обнаружен ID поста.', 'error')
        return redirect('/', 303)
    elif request.form.get('comment_id', None) is None:
        flash('Ошибка изменения статуса задания, не обнаружен ID комментария.', 'error')
        return redirect('/', 303)
    elif request.form.get('task_status', None) != 'Сделано' and request.form.get('task_status', None) != 'В процессе':
        flash(f'Ошибка изменения статуса задания, статуса «{request.form.get("task_status", None)}» не существует.', 'error')
        return redirect('/', 303)
    await edit_status_of_user_task(int(request.form.get('group_id')), int(request.form.get('user_id')), int(request.form.get('task_number')), int(request.form.get('post_id')), int(request.form.get('comment_id')), str(request.form.get('task_status')))
    return redirect('/', 303)

@app.get('/tasks_by_category')
@login_required
async def tasks_by_category():
    """Список заданий - ДЗ по категориям"""
    if request.args.get('group_id', None) is None:
        flash('Произошла ошибка загрузки заданий, не обнаружено ID группы.', 'error')
        return abort(400)
    elif request.args.get('category', None) is None:
        flash('Произошла ошибка загрузки заданий, не обнаружена категория задания.', 'error')
        return abort(400)
    elif request.args.get('category', None) != 'inspection' and request.args.get('category', None) != 'execution' and request.args.get('category', None) != 'completed':
        flash('Произошла ошибка загрузки списка пользователей, выбранный список не существует.', 'error')
        return abort(400)
    
    list_tasks_posts_and_comments = await loading_list_of_user_tasks_by_category(int(request.args.get('group_id')), str(request.args.get('category')))
    table_settings = await loading_group_table_settings(int(request.args.get('group_id')))

    response = make_response(render_template('list_of_posts_and_comments_by_category.html', list_posts=list_tasks_posts_and_comments, table_settings=table_settings, category=request.args.get('category')))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/marathon_groups')
@login_required
async def curator_marathon_groups():
    """
    Список всех марафонских групп и таблиц добавленных в панель
    """
    list_marathon_groups = await loading_list_of_marathon_groups()
    list_marathon_tables = await list_of_google_tables()

    #Установка заголовков ответа сервера
    response = make_response(render_template('list_marathon_groups.html', list_groups=list_marathon_groups, list_tables=list_marathon_tables))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/marathon_group_settings')
@login_required
async def marathon_group_settings():
    """Список настроек конкретной группы"""
    if request.args.get('group_id', None) is None:
        flash('Произошла ошибка загрузки настроек группы марафона. Не найдено ID группы.', 'error')
        return abort(400)
    group_settings = await loading_marathon_group_settings(int(request.args.get('group_id')))

    #Установка заголовков ответа сервера
    response = make_response(render_template('marathon_group_settings.html', group_settings=group_settings))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.post('/edit_group_settings')
@login_required
async def edit_group_settings():
    """Редактирование настроек группы"""
    if request.form.get('group_id', None) is None:
        flash('Произошла ошибка изменения настроек, не найдено ID группы.', 'error')
        return abort(400)
    await edit_marathon_group_settings(int(request.form.get('group_id')))
    return redirect('/', 303)

@app.get('/curators_to_add_to_group')
@login_required
async def curators_to_add_to_group():
    """
    Список кураторов, которых можно добавить к группам марафона, главное, чтобы они ранее не были прикреплены к группе, в которую нужно его добавить
    """
    if request.args.get('group_id', None) is None:
        flash('Произошла ошшибка загрузки списка кураторов с возможностью добавления в группу. Не найдено ID группы.', 'error')
        return abort(400)
    
    list_curators = await loading_list_of_curators_to_add_to_group(int(request.args.get('group_id')))
    #Установка заголовков ответа сервера
    response = make_response(render_template('list_of_curators_to_add_to_group.html', list_curators=list_curators[0], group_id=list_curators[1]))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/curators_in_marathon_groups')
@login_required
async def curators_in_marathon_groups():
    """Отдаёт список кураторов, прикреплённых к группам марафонов"""
    list_curators_in_groups = await loading_list_curators_in_marathon_groups()

    #Установка заголовков ответа сервера
    response = make_response(render_template('list_curators_in_marathon_groups.html', list_groups=list_curators_in_groups))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/tables_in_the_panel')
@login_required
async def tables_in_the_panel():
    """Отдаёт список Google таблиц, добавленных в панель"""
    list_marathon_tables = await list_of_google_tables()

    #Установка заголовков ответа сервера
    response = make_response(render_template('list_marathon_tables.html', list_tables=list_marathon_tables))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.post('/access_rights_in_the_panel')
@login_required
def access_rights_in_the_panel():
    """
    URL отвечает за выдачу/отзыв прав у пользователей доступа к панели управления.
    Можно предоставить/отозвать доступ к панели через ссылку на VK профиль пользователя.
    """
    if request.form.get('method', None) is None:
        return abort(400)
    if request.form.get('method', None) == 'granting_access_id':
        if request.form.get('access_name', None) is None:
            return abort(400)
        granting_rights_in_the_panel(request.form.get('access_name'), int(request.form.get('user_id')))
    elif request.form.get('method') == 'revocation_of_access_id':
        revocation_of_rights_in_the_panel(int(request.form.get('user_id')))
    else:
        if request.form.get('link_to_the_user', None) is None:
            return abort(400)
        user_account = str(request.form.get('link_to_the_user')).replace('https://vk.com/id', '').replace('https://m.vk.com/id', '').replace('https://vk.com/', '').replace('https://m.vk.com/', '')

        if not user_account:
            flash('Произошла ошибка поиска данных аккаунта, проверьте правильность введённых данных.', 'error')
            return abort(400)

        try:
            data_user = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': f'{user_account}', 'fields': 'photo_200'}, timeout=10).json()['response'][0]
        except Timeout:
            flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
            return abort(400)
        except KeyError:
            flash('Произошла ошибка валидации данных аккаунта, сообщите об этом администрации.', 'error')
            return abort(400)
        
        user_id = check_user_in_database(data_user.get('id'))

        if request.form.get('method') == 'granting_access_link':
            if request.form.get('access_name', None) is None:
                return abort(400)
            granting_rights_in_the_panel(request.form.get('access_name'), user_id)
        elif request.form.get('method') == 'revocation_of_access_link':
            revocation_of_rights_in_the_panel(user_id)
    return redirect('/', 303)

@app.post('/managing_marathon_groups')
@login_required
def managing_marathon_groups():
    """URL отвечает за управление группами марафонов: добавление/удаление группы, добавление/удаление куратора к конкретной группе, перевод кураторов между группами"""
    if request.form.get('method', None) is None:
        flash('Метод действия не обнаружен, проверьте корректность данных.', 'error')
        return redirect('/', 303)
    elif request.form.get('method', None) == 'add_marathon_group':
        if request.form.get('token_group', None) is None:
            flash('Токен группы не обнаружен, проверьте правильность введённых данных.', 'error')
            return redirect('/', 303)
        try:
            data_group = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(request.form.get('token_group')), timeout=10).json()['response'][0]
        except Timeout:
            flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
            return redirect('/', 303)
        except KeyError:
            flash('Произошла ошибка валидации данных группы, сообщите об этом администрации.', 'error')
            return redirect('/', 303)
        if data_group.get('id', None) is None or data_group.get('name', None) is None:
            flash('Данные о группе не обнаружены, возможно токен недействителен.', 'error')
            return redirect('/', 303)
        add_marathon_group(int(data_group.get('id')), str(data_group.get('name')))
    elif request.form.get('method', None) == 'delete_marathon_group_id':
        if request.form.get('group_id', None) is None:
            flash('Номер группы не обнаружен, перезагрузите страницу и попробуйте снова.', 'error')
            return redirect('/', 303)
        delete_marathon_group(int(request.form.get('group_id')))
    elif request.form.get('method', None) == 'delete_marathon_group_link':
        if request.form.get('link_to_the_group', None) is None:
            flash('Ссылка на группу не обнаружена, проверьте корректность введёных данных.', 'error')
            return redirect('/', 303)
        try:
            data_group = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'group_id': f'{str(request.form.get("link_to_the_group")).replace("https://m.vk.com/club", "").replace("https://m.vk.com/", "").replace("https://vk.com/club", "").replace("https://vk.com/", "")}'}, timeout=10).json()['response'][0]
        except Timeout:
            flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
            return abort(400)
        except KeyError:
            flash('Произошла ошибка валидации данных группы, сообщите об этом администрации.', 'error')
            return redirect('/', 303)
        if data_group.get('id', None) is None:
            flash('Произошла ошибка получения данных о группе, сообщите об этом администрации.', 'error')
            return redirect('/', 303)
        delete_marathon_group(int(data_group.get('id')))
    elif request.form.get('method', None) == 'removing_curator_from_group':
        if request.form.get('user_id', None) is None:
            flash('Номер куратора не обнаружен, перезагрузите страницу и попробуйте снова.', 'error')
            return redirect('/', 303)
        elif request.form.get('group_id', None) is None:
            flash('Номер группы не обнаружен, перезагрузите страницу и попробуйте снова.', 'error')
            return redirect('/', 303)
        removing_curator_from_marathon_group(int(request.form.get('user_id')), int(request.form.get('group_id')))
    elif request.form.get('method', None) == 'transfer_of_the_curator':
        if request.form.get('user_id', None) is None:
            flash('Номер куратора не обнаружен, перезагрузите страницу и попробуйте снова.', 'error')
            return redirect('/', 303)
        elif request.form.get('group_id', None) is None:
            flash('Номер группы из которой нужно перевести не обнаружен, перезагрузите страницу и попробуйте снова.', 'error')
            return redirect('/', 303)
        elif request.form.get('which_group_id', None) is None:
            flash('Номер группы в которую нужно перевести не обнаружен, перезагрузите страницу и попробуйте снова.', 'error')
            return redirect('/', 303)
        transfer_of_the_curator_from_group_to_group(int(request.form.get('user_id')), int(request.form.get('group_id')), int(request.form.get('which_group_id')))
    elif request.form.get('method', None) == 'adding_curator_to_group':
        if request.form.get('group_id', None) is None:
            flash('Произошла ошибка добавления куратора в группу, не найдено ID группы.', 'error')
            return abort(400)
        elif request.form.get('curator_id', None) is None:
            flash('Произошла ошибка добавления куратора в группу, не найдено ID куратора.', 'error')
            return abort(400)
        add_curator_to_group(int(request.form.get('curator_id')), int(request.form.get('group_id')))
    return redirect('/', 303)

@app.post('/managing_google_spreadsheet')
@login_required
async def managing_google_spreadsheet():
    """URL отвечает за управление - действия с google таблицами: добавление, удаление, прикрепление к конкретной группе"""
    if request.form.get('method', None) is None:
        flash('Метод действия не обнаружен, проверьте корректность данных.', 'error')
        return redirect('/', 303)
    elif request.form.get('method', None) == 'add_google_spreadsheet':
        if request.form.get('link_to_the_table', None) is None:
            flash('Ссылка на таблицу Google не обнаружена, проверьте правильность введённых данных.', 'error')
            return redirect('/', 303)
        await adding_google_tables(str(request.form.get('link_to_the_table')))
    elif request.form.get('method', None) == 'delete_google_spreadsheet':
        if request.form.get('table_id', None) is None:
            flash('Номер таблицы Google не обнаружен, повторите попытку позже.', 'error')
            return redirect('/', 303)
        await delete_google_tables(int(request.form.get('table_id')))
    elif request.form.get('method', None) == 'binding_google_spreadsheet_to_group':
        if request.form.get('table_id', None) is None:
            flash('Номер таблицы Google не обнаружен, повторите попытку позже.', 'error')
            return redirect('/', 303)
        elif request.form.get('group_id', None) is None:
            flash('Номер группы не обнаружен, повторите попытку позже.', 'error')
            return redirect('/', 303)
        await linking_table_to_marathon_group(int(request.form.get('group_id')), int(request.form.get('table_id')))
    return redirect('/', 303)

@app.get('/users_with_requested_access_to_the_panel')
@login_required
async def users_with_requested_access_to_the_panel():
    """Пользователи запросившие доступ к панели управления"""
    list_users = await list_users_with_access_to_the_panel(requested=True)

    #Установка заголовков ответа сервера
    response = make_response(render_template('list_users_with_requested_access_to_the_panel.html', list_users=list_users))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/users_have_access_to_the_panel')
@login_required
async def users_have_access_to_the_panel():
    """Пользователи, которые имеют доступ к панели управления"""
    list_users = await list_users_with_access_to_the_panel(issued=True)

    #Установка заголовков ответа сервера
    response = make_response(render_template('list_of_users_with_access_to_the_panel.html', list_users=list_users))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.post('/managing_access_to_the_panel')
@login_required
async def managing_access_to_the_panel():
    """Url отвечает за выдачу и/или отзыв прав к доступу входа в панель"""
    if request.form.get('method', None) is None:
        flash('Метод действия не обнаружен, проверьте корректность данных.', 'error')
        return redirect('/', 303)
    elif request.form.get('method', None) == 'granting_access_to_the_panel':
        if request.form.get('vk_link', None) is None:
            flash('Не найдена ссылка на пользователя, проверьте корректность данных.', 'error')
            return redirect('/', 303)
        await granting_the_user_access_to_the_panel(str(request.form.get('vk_link')))
    elif request.form.get('method', None) == 'removing_user_access_to_the_panel':
        if request.form.get('vk_link', None) is None:
            flash('Не найдена ссылка на пользователя, проверьте корректность данных.', 'error')
            return redirect('/', 303)
        await removing_user_access_to_the_panel(str(request.form.get('vk_link')))
    return redirect('/', 303)

@app.route('/user_notifications', methods=['GET'])
def user_notifications():
    """При обращении по данному url, сервер отправляет html разметку с текстом уведомления"""
    json_notifications = {}
    for notifications in get_flashed_messages(with_categories=True):
        json_notifications.update({'message': notifications[1], 'category': notifications[0]})
    response = make_response(render_template('notifications/user_flash_notifications.html', json_notifications=json_notifications))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.post('/login')
def login_post():
    if request.form.get('method', None) is None:
        flash('Произошла ошибка, не найден метод действия, повторите попытку запроса доступа.', 'error')
        return abort(400)
    if request.form.get('method') == 'request_access':
        if session.get('user_vk_id', None) is None:
            flash('Произошла ошибка, не найдены данные аккаунта, повторите попытку запроса доступа.', 'error')
            return abort(400)
        user = users_with_access_to_the_panel.query.filter_by(vk_id=int(session['user_vk_id'])).first()
        if user is not None:
            flash('Вы уже запрашивали доступ к панели, повторный запрос не требуется.', 'error')
            return abort(400)
        else:
            user = users_with_access_to_the_panel(vk_id=int(session['user_vk_id']))
            db.session.add(user)
            db.session.commit()
        flash('Доступ успешно запрошен, ожидайте выдачи доступа к панели.', 'info')
        return redirect('/login', 303)
    else:
        flash('Произведено неизвестное действие, возможно Вы делаете что-то неправильно.', 'error')
        return redirect('/login', 303)

@app.get('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.args.get('uid', None) is not None:
        # hash = f"{}{request.args.get('uid')}{}" #{id - номер приложения в VK, отвечающего за авторизацию пользователей}{uid - id страницы пользователя в VK}{secret key приложения, отвечающего за авторизацию пользователей}
        # if str(request.args.get('hash')) != str(hashlib.md5(hash.encode()).hexdigest()):
        #     return redirect(url_for('index'))
        user_request = users_with_access_to_the_panel.query.filter_by(vk_id=int(request.args.get('uid'))).first()
        if user_request is None:
            session['user_vk_id'] = int(request.args.get('uid'))
            response = make_response(render_template('login/request_access_to_the_panel.html', vk_id=int(request.args.get('uid'))))
            response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        elif user_request is not None and user_request.access == 'Запрошен':
            flash('Вам ещё не выдали доступ к панели, ожидайте.', 'error')
            return redirect(url_for('login'))
        elif user_request is not None and user_request.access == 'Выдан':
            info_user = User.query.filter_by(vk_id=int(request.args.get('uid'))).first()
            if info_user is None:
                user = User(vk_id=int(request.args.get('uid')))
                db.session.add(user)
                db.session.commit()
                info_user = User.query.filter_by(vk_id=int(request.args.get('uid'))).first()
            session.pop('user_vk_id', None)
            login_user(info_user, remember=True)
            flash('Вы успешно вошли в свой аккаунт. Добро пожаловать в панель управления.', 'info')
            return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(vk_id=form.vk_id.data).first()
        if user is None:
            flash('Invalid VK_ID')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    #Установка заголовков ответа сервера
    response = make_response(render_template('login/login.html', form=form))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))