import requests
from requests.exceptions import Timeout
import os
import ast
import json
import time
from pprint import pprint as print
import secrets
import re
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime
from flask import flash, request, abort
from flask_login import current_user
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models import User, marathon_groups, list_of_user_groups, panel_access_rights, user_access_rights_in_the_panel, names_of_marathon_groups, name_of_environment_variable_of_marathon_groups, \
    users_who_have_add_marathon_groups, access_rights_for_curators_in_groups, google_marathon_tables, tables_linked_to_marathon_groups, table_column_settings, user_name_column_in_the_table, \
    user_last_name_column_in_the_table, user_reference_column_in_the_table, user_group_column_in_the_table, user_name_cabinet_column_in_the_table, headings_column_in_the_table, stop_content_column_in_the_table, \
    ad_text_column_in_the_table, ad_media_column_in_the_table, target_audience_column_in_the_table, request_stop_column_in_the_table, launch_status_column_in_the_table, number_of_tasks_in_the_marathon_table, \
    tasks_column_in_the_table, initial_word_user_name_column_in_the_table, initial_word_user_last_name_column_in_the_table, initial_word_user_reference_column_in_the_table, initial_word_user_group_column_in_the_table, \
    initial_word_user_name_cabinet_column_in_the_table, initial_word_headings_column_in_the_table, initial_word_stop_content_column_in_the_table, initial_word_ad_text_column_in_the_table, initial_word_ad_media_column_in_the_table, \
    initial_word_target_audience_column_in_the_table, initial_word_request_stop_column_in_the_table, initial_word_launch_status_column_in_the_table, initial_word_tasks_column_in_the_table, marathon_group_settings, \
    name_of_the_marathon_group_table_sheet, marathon_users, status_of_marathon_users_tasks, information_about_the_post_with_the_task, users_with_access_to_the_panel, group_server_callback_api_data, posts_in_groups
from app import app, db

async def loading_list_of_curator_groups() -> list:
    """Загрузка групп которые курирует текущий куратор"""
    list_groups_user = [group.group_id for group in marathon_groups.query
                        .join(list_of_user_groups, marathon_groups.id == list_of_user_groups.group_id)
                        .filter_by(user_id=current_user.id)
                        .all()]
    if list_groups_user == []:
        flash('Ошибка загрузки групп которые Вы курируете, у Вас нет групп под Вашем кураторством.', 'error')
        return []
    data_response_groups = []
    for group in list_groups_user:
        name_environment = f'group_{group}'
        if os.environ.get(name_environment, None) is None:
            continue
        try:
            group_data = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(os.environ.get(name_environment)), data = {'group_ids': f'{group}', 'fields': 'description, members_count, status, verified, wiki_page'}, timeout=10).json()['response']
        except (Timeout, KeyError):
            continue
        data_response_groups.append(group_data[0])
    json_group_data = {}
    for group_data in data_response_groups:
        json_group_data.update({group_data['id']: {'name': group_data['name'], 'screen_name': group_data['screen_name'], 'photo_200': group_data['photo_200'], 'members_count': group_data['members_count']}})
    users_groups_data = []
    for group in list_groups_user:
        users_groups_data.append(json.loads(str({"group_id": group, "name": json_group_data.get(group)['name'], "screen_name": json_group_data.get(group)['screen_name'], "photo_200": json_group_data.get(group)['photo_200'], "members_count": json_group_data.get(group)['members_count']}).replace("'", '"')))
    return users_groups_data

async def loading_group_data(group_id: int) -> dict:
    """Получение всей информации о группе марафона, название, id, фото, переменные окружения, информацию о привязанной таблице"""
    info_group = db.session.query(marathon_groups).filter(marathon_groups.group_id == group_id).options(joinedload(marathon_groups.name_group), joinedload(marathon_groups.name_environment), joinedload(marathon_groups.google_table)).first()
    try:
        data_marathon_group = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(os.environ.get(info_group.name_environment.name)), timeout=10).json()['response'][0]
    except Timeout:
        flash('Произошла ошибка загрузки данных о группе марафона, истекло время ожидания ответа от серверов ВК, повторите попытку чуть позже.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка при получении данных о группе марафона, проблема со стороны ВК.', 'error')
        return []
    except IndexError:
        flash(f'Произошла ошибка, при получении данных о группе марафона, проблема либо со стороны ВК, либо токен группы «{info_group.name_group.name}» недействителен.', 'error')
        return []
    if str(data_marathon_group['name']) != str(info_group.name_group.name):
        info_group_name = names_of_marathon_groups.query.filter_by(group_id=info_group.id).one()
        info_group_name.name = str(data_marathon_group['name'])
        db.session.add(info_group_name)
        db.session.commit()
    return [
        json.loads(str(
        {"id": info_group.id, 
         "group_id": info_group.group_id, 
         "name_group": info_group.name_group.name if str(data_marathon_group['name']) == str(info_group.name_group.name) else data_marathon_group['name'], 
         "photo_group_200": data_marathon_group.get("photo_200", None), 
         "environment": info_group.name_environment.name, 
         "google_table": [{"id": info_group.google_table.link_table.id, 
                           "link": info_group.google_table.link_table.link_to_the_table, 
                           "time_of_addition": datetime.fromtimestamp(info_group.google_table.link_table.time_of_addition).strftime('%d-%m-%Y, %H:%M:%S')}] if info_group.google_table is not None else [], 
                           "time_of_addition_group": datetime.fromtimestamp(info_group.user_who_added.time_of_addition).strftime('%d-%m-%Y, %H:%M:%S')}).replace("'", '"'))
    ]

async def loading_group_posts(group_id: int) -> list:
    """
    Загружает список всех(если они есть в базе) постов указанной группы.
    """
    info_group = db.session.query(marathon_groups).filter(marathon_groups.group_id == group_id).options(joinedload(marathon_groups.posts)).first()
    if info_group.posts == []:
        flash('Неудалось загрузить посты в группе, посты отсутствуют в базе.', 'error')
        return []
    list_posts_in_group = info_group.posts
    try:
        data_response_posts_in_group = requests.post('https://api.vk.com/method/wall.getById?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'posts': str([str(f"-{group_id}_{post.post_id}") for post in list_posts_in_group]).replace('[', '').replace(']', '').replace("'", '')}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки постов группы, истекло время ожидания ответа от сервера VK.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка загрузки постов группы, проблема со стороны ВК.', 'error')
        return []
    json_data_posts_ids = {}
    for post in data_response_posts_in_group:
        json_data_posts_ids.update({post["id"]: {'id': post["id"], 'count_comments': post["comments"]["count"], 'count_likes': post["likes"]["count"], 'count_reposts': post["reposts"]["count"], 'count_views': post["views"]["count"], 'text': str(post["text"]).replace("<script>", "").replace("</script>", "").replace("<script", "").replace("\n", "<br>"), 'attachments': ast.literal_eval(str(post["attachments"])), 'date_of_publication': datetime.fromtimestamp(post["date"]).strftime("%d-%m-%Y, %H:%M")}})
    posts_group_data = []
    for post in list_posts_in_group:
        posts_group_data.append({"id": post.id, "post_id": post.post_id, "post_count_comments": json_data_posts_ids.get(post.post_id)['count_comments'], "post_count_likes": json_data_posts_ids.get(post.post_id)['count_likes'], "post_count_reposts": json_data_posts_ids.get(post.post_id)['count_reposts'], "post_count_views": json_data_posts_ids.get(post.post_id)['count_views'], "post_text": json_data_posts_ids.get(post.post_id)['text'], "post_attachments": ast.literal_eval(str(json_data_posts_ids.get(post.post_id)['attachments'])), "post_date_of_publication": json_data_posts_ids.get(post.post_id)['date_of_publication']})
    return posts_group_data

async def loading_post_comments(group_id: int, post_id: int, page: int) -> list:
    """
    Возвращает список комментариев под конкретным постом.
    Вернёт пустой список если возникла ошибка или комментариев под постом нет.
    """
    curated_groups = list_of_user_groups.query.filter_by(user_id=current_user.id).all()
    info_group = db.session.query(marathon_groups).filter_by(group_id=group_id).options(joinedload(marathon_groups.marathon_members)).first()
    if info_group is None:
        flash('Произошла ошибка загрузка комментариев под постом, группа марафона не обнаружена, возможно она была удалена.', 'error')
        return []
    dict_status_of_user_tasks = {}
    for user in info_group.marathon_members:
        for task in user.tasks:
            if dict_status_of_user_tasks.get(user.vk_id, None) is None:
                dict_status_of_user_tasks.update({user.vk_id: {task.task_number: {'task_status': task.task_status}}})
            else:
                dict_status_of_user_tasks.get(user.vk_id).update({task.task_number: {'task_status': task.task_status}})
    list_groups_user = [marathon_groups.query.filter_by(id=group.group_id).first().group_id for group in curated_groups]
    if int(group_id) not in list_groups_user:
        flash('Вы не курируете данную группу, доступ запрещён.', 'error')
        return []
    try:
        data_response_comments_one = requests.post('https://api.vk.com/method/wall.getComments?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'owner_id': f'-{group_id}', 'post_id': post_id}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки постов группы, истекло время ожидания ответа от сервера VK.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка загрузки постов группы, проблема со стороны ВК.', 'error')
        return []
    count_comments = data_response_comments_one['current_level_count']
    offset = int(page - 1) * 25 if page != 1 else 0
    if offset >= count_comments:
        flash(f'Невозможно загрузить страницу #{page}, комментарии закончились.', 'error')
        return []
    try:
        data_response_comments_two = requests.post('https://api.vk.com/method/wall.getComments?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'owner_id': f'-{group_id}', 'post_id': post_id, 'count': 100, 'offset': offset, 'extended': 1, 'fields': 'photo_200'}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки постов группы, истекло время ожидания ответа от сервера VK.', 'error')
        return []
    except KeyError:
        flash(f'Произошла ошибка загрузки постов группы, проблема со стороны ВК.', 'error')
        return []
    json_user_profiles = {}
    for user in data_response_comments_two['profiles']:
        json_user_profiles.update({user['id']: {'user_id': user['id'], 'user_first_name': user['first_name'], 'user_last_name': user['last_name'], 'user_photo_200': user['photo_200']}})
    json_group_profiles = {}
    for group in data_response_comments_two['groups']:
        json_group_profiles.update({group['id']: {'group_id': group['id'], 'group_name': group['name'], 'group_photo_200': group['photo_200']}})
    data_comments_in_post = []
    for comment in data_response_comments_two['items']:
        text_in_comment = str(comment['text']).replace("<script>", "").replace("</script>", "").replace("<script", "").replace("\n", "<br>")
        list_links_in_text = re.findall(r'(https?://\S+)', comment['text'])
        for link in list_links_in_text:
            text_in_comment = text_in_comment.replace(link, f'<a href="{link}" class="text-decoration-none">{link}</a>')
        if int(comment['from_id']) >= 1:
            data_comments_in_post.append({'group_id': group_id,
                                          'comment_id': comment['id'], 
                                          'comment_from_id': comment['from_id'], 
                                          'comment_post_id': comment['post_id'], 
                                          'comment_text': text_in_comment, 
                                          'comment_date': datetime.fromtimestamp(comment['date']).strftime('%d-%m-%Y, %H:%M'), 
                                          'commentator_data': {'user_id': json_user_profiles.get(comment['from_id'])['user_id'], 
                                                               'user_first_name': json_user_profiles.get(comment['from_id'])['user_first_name'], 
                                                               'user_last_name': json_user_profiles.get(comment['from_id'])['user_last_name'], 
                                                               'user_photo_200': json_user_profiles.get(comment['from_id'])['user_photo_200'], 
                                                               'user_vk_link': f'https://vk.com/id{json_user_profiles.get(comment["from_id"])["user_id"]}'}, 'comment_attachments': ast.literal_eval(str(comment["attachments"])) if comment.get('attachments', None) is not None else []})
        else:
            from_id = int(str(comment['from_id']).replace('-', ''))
            data_comments_in_post.append({'group_id': group_id,
                                          'comment_id': comment['id'], 
                                          'comment_from_id': from_id, 
                                          'comment_post_id': comment['post_id'], 
                                          'comment_text': text_in_comment, 
                                          'comment_date': datetime.fromtimestamp(comment['date']).strftime('%d-%m-%Y, %H:%M'), 
                                          'commentator_data': {'group_id': json_group_profiles.get(from_id)['group_id'], 
                                                               'group_name': json_group_profiles.get(from_id)['group_name'], 
                                                               'group_photo_200': json_group_profiles.get(from_id)['group_photo_200'], 
                                                               'group_vk_link': f'https://vk.com/club{json_group_profiles.get(from_id)["group_id"]}'}, 
                                          'comment_attachments': ast.literal_eval(str(comment["attachments"])) if comment.get('attachments', None) is not None else []})
    return [data_comments_in_post, dict_status_of_user_tasks, {'count_comments': count_comments, 
                                                               'count_page': round(count_comments/25)}
                                                               ]

async def loading_list_post_comment_thread(group_id: int, post_id: int, comment_id: int) -> list:
    """
    Загружает ветку комментариев(если они есть) под комментарием, определённого поста и группы.
    Возвращает пустой список если произошла ошибка или ветки комментариев у коммента нет.
    """
    curated_groups = list_of_user_groups.query.filter_by(user_id=current_user.id).all()

    list_groups_user = [marathon_groups.query.filter_by(id=group.group_id).first().group_id for group in curated_groups]
    if int(group_id) not in list_groups_user:
        flash('Вы не курируете данную группу, доступ запрещён.', 'error')
        return []
    
    try:
        data_response_comment_thread = requests.post('https://api.vk.com/method/wall.getComments?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'owner_id': f'-{group_id}', 'post_id': post_id, 'extended': 1, 'fields': 'photo_200', 'comment_id': comment_id}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки ветки комментария под постом, истекло время ожидания ответа от сервера VK.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка загрузки ветки комментария под постом, проблема со стороны ВК.', 'error')
        return []
    
    json_user_profiles = {}
    if data_response_comment_thread.get('profiles', None) is not None:
        for user in data_response_comment_thread['profiles']:
            json_user_profiles.update({user['id']: {'user_id': user['id'], 'user_first_name': user['first_name'], 'user_last_name': user['last_name'], 'user_photo_200': user['photo_200'], 'user_profile_link_in_vk': f'https://vk.com/id{user["id"]}'}})
    
    json_group_profiles = {}
    if data_response_comment_thread.get('groups', None) is not None:
        for group in data_response_comment_thread['groups']:
            json_group_profiles.update({group['id']: {'group_id': group['id'], 'group_name': group['name'], 'group_photo_200': group['photo_200'], 'group_link_in_vk': f'https://vk.com/club{group["id"]}'}})
    
    list_comments_in_thread = []
    for comment in data_response_comment_thread['items']:
        text_comment = str(comment['text']).replace("<script>", "").replace("</script>", "").replace("<script", "").replace("\n", "<br>")
        list_links_in_text = re.findall(r'(https?://\S+)', comment['text'])
        list_mentions_text = re.findall(r'\[id[0-9]+\|\w+\]', comment['text'])

        for user in list_mentions_text:
            user_id = re.search(r'[0-9]+', user)[0]
            user_name = re.search(r'(\|\w+)', user)[0].replace('|', '')
            text_comment = text_comment.replace(user, f'<a href="https://vk.com/id{user_id}" class="text-decoration-none">{user_name}</a>')
        for link in list_links_in_text:
            text_comment = text_comment.replace(link, f'<a href="{link}" class="text-decoration-none">{link}</a>')
        
        if int(comment['from_id']) >= 1:
            list_comments_in_thread.append({
                'group_id': group_id,
                'post_id': comment['post_id'],
                'comment_id': comment['id'],
                'comment_from_id': comment['from_id'],
                'comment_date': datetime.fromtimestamp(comment['date']).strftime('%d-%m-%Y, %H:%M'),
                'comment_text': text_comment,
                'commentator_data': {'user_id': json_user_profiles.get(comment['from_id'])['user_id'], 
                                    'user_first_name': json_user_profiles.get(comment['from_id'])['user_first_name'], 
                                    'user_last_name': json_user_profiles.get(comment['from_id'])['user_last_name'], 
                                    'user_photo_200': json_user_profiles.get(comment['from_id'])['user_photo_200'], 
                                    'user_vk_link': f'https://vk.com/id{json_user_profiles.get(comment["from_id"])["user_id"]}'
                                    },
                'comment_attachments': ast.literal_eval(str(comment["attachments"])) if comment.get('attachments', None) is not None else []
            })
        else:
            from_id = int(str(comment['from_id']).replace('-', ''))
            list_comments_in_thread.append({'group_id': group_id,
                                            'post_id': comment['post_id'],
                                            'comment_id': comment['id'],
                                            'comment_from_id': comment['from_id'],
                                            'comment_date': datetime.fromtimestamp(comment['date']).strftime('%d-%m-%Y, %H:%M'),
                                            'comment_text': text_comment,
                                            'commentator_data': {'group_id': json_group_profiles.get(from_id)['group_id'], 
                                                                'group_name': json_group_profiles.get(from_id)['group_name'], 
                                                                'group_photo_200': json_group_profiles.get(from_id)['group_photo_200'], 
                                                                'group_vk_link': f'https://vk.com/club{json_group_profiles.get(from_id)["group_id"]}'}, 
                                            'comment_attachments': ast.literal_eval(str(comment["attachments"])) if comment.get('attachments', None) is not None else []})
    return list_comments_in_thread

async def loading_list_of_user_tasks_by_category(group_id: int, category: str = 'inspection') -> list:
    info_group = db.session.query(marathon_groups).filter_by(group_id=group_id).options(joinedload(marathon_groups.posts)).first()
    if info_group is None:
        flash('Произошла ошибка загрузки заданий пользователей, группа не обнаружена, возможно она была удалена.', 'error')
        return []
    list_users = db.session.query(marathon_users).join(marathon_groups).all()
    if list_users == []:
        flash('Произошла ошибка загрузки списка заданий пользователей, данные о заданиях отсутствуют в базе.', 'error')
        return []
    if category == 'inspection':
        list_of_tasks = [user.tasks for user in list_users]
        list_of_comments = {}
        for info_task in list_of_tasks:
            for task in info_task:
                if list_of_comments.get(task.info_post.post_id, None) is None:
                    list_of_comments.update({task.info_post.post_id: [task.info_post.comment_id]})
                elif list_of_comments.get(task.info_post.post_id, None) is not None and task.info_post.comment_id not in list_of_comments.get(task.info_post.post_id):
                    list_of_comments[task.info_post.post_id] = list_of_comments.get(task.info_post.post_id) + [task.info_post.comment_id]
    elif category == 'execution':
        list_of_tasks = [user.tasks for user in list_users]
        list_of_comments = {}
        for info_task in list_of_tasks:
            for task in info_task:
                if task.task_status == 'В процессе':
                    if list_of_comments.get(task.info_post.post_id, None) is None:
                        list_of_comments.update({task.info_post.post_id: [task.info_post.comment_id]})
                    elif list_of_comments.get(task.info_post.post_id, None) is not None and task.info_post.comment_id not in list_of_comments.get(task.info_post.post_id):
                        list_of_comments[task.info_post.post_id] = list_of_comments.get(task.info_post.post_id) + [task.info_post.comment_id]
    elif category == 'completed':
        list_of_tasks = [user.tasks for user in list_users]
        list_of_comments = {}
        for info_task in list_of_tasks:
            for task in info_task:
                if task.task_status == 'Сделано':
                    if list_of_comments.get(task.info_post.post_id, None) is None:
                        list_of_comments.update({task.info_post.post_id: [task.info_post.comment_id]})
                    elif list_of_comments.get(task.info_post.post_id, None) is not None and task.info_post.comment_id not in list_of_comments.get(task.info_post.post_id):
                        list_of_comments[task.info_post.post_id] = list_of_comments.get(task.info_post.post_id) + [task.info_post.comment_id]
    try:
        data_response_posts = requests.post('https://api.vk.com/method/wall.getById?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'posts': str([str(f"-{group_id}_{post.post_id}") for post in info_group.posts]).replace('[', '').replace(']', '').replace("'", '')}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки постов группы, истекло время ожидания ответа от сервера VK.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка загрузки постов группы, проблема со стороны ВК.', 'error')
        return []
    list_data_posts = []
    dict_post_in_group = {}
    for post in data_response_posts:
        loop = True
        current_page = 1
        dict_post_in_group.update({post["id"]: []})
        while loop is True:
            post_comments = []
            post_comments = await loading_post_comments(group_id, post["id"], current_page)
            if post_comments != []:
                current_page += 1
                dict_post_in_group[post["id"]] = dict_post_in_group.get(post["id"]) + post_comments
            else:
                loop = False
        list_data_posts.append({'id': post["id"], 'count_comments': post["comments"]["count"], 'count_likes': post["likes"]["count"], 'count_reposts': post["reposts"]["count"], 'count_views': post["views"]["count"], 'text': str(post["text"]).replace("<script>", "").replace("</script>", "").replace("<script", "").replace("\n", "<br>"), 'attachments': ast.literal_eval(str(post["attachments"])), 'date_of_publication': datetime.fromtimestamp(post["date"]).strftime("%d-%m-%Y, %H:%M"), 'comments': dict_post_in_group.get(post["id"])})
    return [list_data_posts, list_of_comments]

async def sending_the_curator_response_to_comment(group_id: int, post_id: int, comment_id: int) -> None:
    """
    Отправляет ответный комментарий на комментарий под постом.
    """
    if request.files.getlist('comment_attachments') != []:
        list_file_name_attachments = []
        list_photo_attachments = []
        list_video_attachments = []
        #list_docs_attachments = []
        list_of_final_attachments = []
        for uploaded_file in request.files.getlist('comment_attachments'):
            if uploaded_file.filename != '':
                file_ext = os.path.splitext(uploaded_file.filename)[1]
                file_name = secrets.token_hex()
                if file_ext in ['.jpg', '.png']:
                    list_photo_attachments.append(f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')
                    list_file_name_attachments.append(f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')
                    uploaded_file.save(os.path.join('app/static/response_to_comment_attachments', str(uploaded_file.filename).replace(f'{uploaded_file.filename}', f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')))
                elif file_ext in ['.mp4', '.mov', '.avi', '.mpeg', '.mp3', '.flv', '.wmv']:
                    list_video_attachments.append(f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')
                    list_file_name_attachments.append(f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')
                    uploaded_file.save(os.path.join('app/static/response_to_comment_attachments', str(uploaded_file.filename).replace(f'{uploaded_file.filename}', f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')))
                # если нужно чтобы через панель можно было отправлять гифки - раскоменьть
                # elif file_ext in ['.gif']:
                #     list_docs_attachments.append(f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')
                #     list_file_name_attachments.append(f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')
                #     uploaded_file.save(os.path.join('app/static/response_to_comment_attachments', str(uploaded_file.filename).replace(f'{uploaded_file.filename}', f'{file_name}{os.path.splitext(uploaded_file.filename)[1]}')))
        if list_photo_attachments != []:
            try:
                data_upload_server = requests.post('https://api.vk.com/method/photos.getUploadServer?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'album_id': '293832343'}, timeout=10).json()['response']
            except Timeout:
                flash('Произошла ошибка загрузки данных о альбоме для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
                return []
            except KeyError:
                flash('Произошла ошибка загрузки данных о альбоме для загрузки вложений, проблема со стороны ВК.', 'error')
                return []
            multiple_files = []
            iteration_number = 0
            for file in list_photo_attachments:
                iteration_number += 1
                multiple_files.append((f'file{iteration_number}', (f'{file}', open(f'app/static/response_to_comment_attachments/{file}', 'rb'), f'image/{file.split(".")[1]}')))
            try:
                data_upload = requests.post(f'{data_upload_server["upload_url"]}', files=multiple_files, timeout=10).json()
            except Timeout:
                flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
                return []
            except KeyError:
                flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, проблема со стороны ВК.', 'error')
                return []
            try:
                data_load_photo = requests.post('https://api.vk.com/method/photos.save?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'album_id': '293832343', 'server': data_upload["server"], 'photos_list': str(data_upload["photos_list"]), 'hash': data_upload["hash"]}, timeout=10).json()['response']
            except Timeout:
                flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
                return []
            except KeyError:
                flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, проблема со стороны ВК.', 'error')
                return []
            for attachment in data_load_photo:
                list_of_final_attachments.append(f'photo{attachment["owner_id"]}_{attachment["id"]}')
        # если нужно чтобы через панель можно было отправлять гифки - раскоменьть
        # if list_docs_attachments != []:
        #     try:
        #         data_upload_server = requests.post('https://api.vk.com/method/docs.getUploadServer?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), timeout=10).json()['response']
        #     except Timeout:
        #         flash('Произошла ошибка загрузки данных о документе для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
        #         return []
        #     except KeyError:
        #         flash('Произошла ошибка загрузки данных о документе для загрузки вложений, проблема со стороны ВК.', 'error')
        #         return []
        #     multiple_files = []
        #     for file in list_docs_attachments:
        #         multiple_files.append(('file', (f'{file}', open(f'app/static/response_to_comment_attachments/{file}', 'rb'), f'document/{file.split(".")[1]}')))
        #     try:
        #         data_upload = requests.post(f'{data_upload_server["upload_url"]}', files=multiple_files, timeout=10).json()
        #     except Timeout:
        #         flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
        #         return []
        #     except (KeyError, JSONDecodeError):
        #         flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, проблема со стороны ВК.', 'error')
        #         return []
        #     try:
        #         data_load_docs = requests.post('https://api.vk.com/method/docs.save?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data = {'file': str(data_upload["file"])}, timeout=10).json()['response']['doc']
        #     except Timeout:
        #         flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
        #         return []
        #     except KeyError:
        #         flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, проблема со стороны ВК.', 'error')
        #         return []
        #     print(data_load_docs)
        #     print(list_of_final_attachments)
        #     list_of_final_attachments.append(f'doc{data_load_docs["owner_id"]}_{data_load_docs["id"]}')
        #     return []
        if list_video_attachments != [] and len(list_video_attachments) == 1:
            try:
                data_upload_server = requests.post('https://api.vk.com/method/video.save?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), timeout=10).json()['response']
            except Timeout:
                flash('Произошла ошибка загрузки данных о альбоме для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
                return []
            except KeyError:
                flash('Произошла ошибка загрузки данных о альбоме для загрузки вложений, проблема со стороны ВК.', 'error')
                return []
            multiple_files = [('video_file', (f'{list_video_attachments[0]}', open(f'app/static/response_to_comment_attachments/{list_video_attachments[0]}', 'rb'), f'video/{list_video_attachments[0].split(".")[1]}'))]
            try:
                data_upload = requests.post(f'{data_upload_server["upload_url"]}', files=multiple_files, timeout=10).json()
            except Timeout:
                flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, истекло время ожидания ответа от сервера VK.', 'error')
                return []
            except KeyError:
                flash('Произошла ошибка загрузки данных о сервере для загрузки вложений, проблема со стороны ВК.', 'error')
                return []
            list_of_final_attachments.append(f'video{data_upload["owner_id"]}_{data_upload["video_id"]}')
    if request.form.get('comment_text', None) is not None and list_of_final_attachments != []:
        try:
            data_upload_server = requests.post('https://api.vk.com/method/wall.createComment?access_token={}&v=5.131'.format(os.environ.get(f"group_{group_id}")), data = {'owner_id': f'-{group_id}', 'post_id': post_id, 'from_group': group_id, 'message': request.form.get("comment_text"), 'reply_to_comment': comment_id, 'attachments': str([attachment for attachment in list_of_final_attachments]).replace("[", "").replace("]", "").replace("'", "")}, timeout=10).json()['response']
        except Timeout:
            flash('Произошла ошибка отправки комментария, истекло время ожидания ответа от сервера VK.', 'error')
            return []
        except KeyError:
            flash('Произошла ошибка отправки комментария, проблема со стороны ВК.', 'error')
            return []
    elif request.form.get('comment_text', None) is not None and list_of_final_attachments == []:
        try:
            data_upload_server = requests.post('https://api.vk.com/method/wall.createComment?access_token={}&v=5.131'.format(os.environ.get(f"group_{group_id}")), data = {'owner_id': f'-{group_id}', 'post_id': post_id, 'from_group': group_id, 'message': request.form.get("comment_text"), 'reply_to_comment': comment_id}, timeout=10).json()['response']
        except Timeout:
            flash('Произошла ошибка отправки комментария, истекло время ожидания ответа от сервера VK.', 'error')
            return []
        except KeyError:
            flash('Произошла ошибка отправки комментария, проблема со стороны ВК.', 'error')
            return []
    elif request.form.get('comment_text', None) is None and list_of_final_attachments != []:
        try:
            data_upload_server = requests.post('https://api.vk.com/method/wall.createComment?access_token={}&v=5.131'.format(os.environ.get(f"group_{group_id}")), data = {'owner_id': f'-{group_id}', 'post_id': post_id, 'from_group': group_id, 'reply_to_comment': comment_id, 'attachments': str([attachment for attachment in list_of_final_attachments]).replace("[", "").replace("]", "").replace("'", "")}, timeout=10).json()['response']
        except Timeout:
            flash('Произошла ошибка отправки комментария, истекло время ожидания ответа от сервера VK.', 'error')
            return []
        except KeyError:
            flash('Произошла ошибка отправки комментария, проблема со стороны ВК.', 'error')
            return []
    return []

async def forming_list_of_the_alphabet_of_the_table(columncount: int) -> list:
    """
    Формирует список англ. букв/связки букв в зависимости от кол-ва столбцов в таблице.
    """
    english_alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    english_alphabet_2 = []
    word_index = 0
    number_of_repetitions = 0
    current_alphabet_iteration = 0
    current_iteration = 0
    while current_iteration < columncount:
        if current_alphabet_iteration < 26:
            if number_of_repetitions == 0:
                word = english_alphabet[current_alphabet_iteration]
            elif number_of_repetitions > 0 and word_index < 26:
                word = str(english_alphabet[word_index]) + str(english_alphabet[current_alphabet_iteration])
            english_alphabet_2.append(word)
            current_alphabet_iteration += 1
        if current_alphabet_iteration >= 26:
            number_of_repetitions += 1
            current_alphabet_iteration = 0
        if current_alphabet_iteration == 0 and number_of_repetitions >= 2:
            word_index += 1
        current_iteration += 1
    return english_alphabet_2

async def loading_the_grid_linked_group_table(group_id: int) -> list:
    """
    Возвращает список состоящий из листов и их контента
    """
    info_group = db.session.query(marathon_groups).filter(marathon_groups.group_id == group_id).options(joinedload(marathon_groups.google_table)).first()
    if info_group.google_table is None:
        flash('Неудалось загрузить привязанную таблицу к группе, возможно она была удалена.', 'error')
        return []
    json_google_table = await get_information_on_the_google_table(info_group.google_table.link_table.link_to_the_table, True)
    if json_google_table is None:
        flash('Произошла ошибка загрузки данных таблицы, не получилось получить данные таблицы.', 'error')
        return []
    if json_google_table.get('sheets', None) is None:
        flash('У привязанной к группе таблицы отсутствуют страницы, загрузка данных невозможна.', 'error')
        return []
    data_list_google_table = {}
    #Формирование данных о каждом из существующих листов таблицы
    for page in json_google_table.get('sheets'):
        if page['properties']['sheetType'] not in ['SHEET_TYPE_UNSPECIFIED', 'OBJECT', 'DATA_SOURCE']:
            data_list_google_table.update({page['properties']['sheetId']: 
                                        {'sheetId': page['properties']['sheetId'], 
                                            'title': page['properties']['title'], 
                                            'index': page['properties']['index'], 
                                            'sheetType': page['properties']['sheetType'],
                                            'tabColorStyle': page['properties']['tabColorStyle'] if page['properties'].get('tabColorStyle', None) is not None else None, 
                                            'gridProperties': page['properties']['gridProperties'],
                                            'gridAlphabet': await forming_list_of_the_alphabet_of_the_table(page['properties']['gridProperties'].get('columnCount', 26))
                                            }
                                            })
        else:
            flash(f'Страница таблицы «{page["properties"]["title"]}» содержит неподдерживаемый тип сетки «{page["properties"]["sheetType"]}», она не будет отображена.', 'error')
    #Получение значений всех ячеек в каждом существующем листе таблицы
    for key in data_list_google_table.keys():
        data_table = data_list_google_table.get(key)
        page_values = await get_values_in_google_spreadsheet(info_group.google_table.link_table.link_to_the_table, data_table['title'], date_time_render_option='FORMATTED_STRING')
        data_table.update({'majorDimension': page_values.get('majorDimension', None), 
                           'range': page_values.get('range', None), 
                           'values': page_values['values'] if page_values.get('values', None) is not None else []
                           })
    return [[{'group_id': group_id, 'table_id': info_group.google_table.link_table.id, 'table_link': info_group.google_table.link_table.link_to_the_table}], [data_list_google_table.get(key) for key in data_list_google_table.keys()]]

async def loading_group_table_settings(group_id: int) -> dict:
    """
    Возвращает словарь состоящий из перечисления данных привязанной к группе таблицы.
    Так же возвращает перечисление всех существующих вариантов контента в колонках.
    """
    info_table = db.session.query(marathon_groups).filter(marathon_groups.group_id == group_id).options(joinedload(marathon_groups.google_table)).first()
    if info_table.google_table is not None:
        table_id = info_table.google_table.table_id
        group_id = info_table.google_table.group_id
        link_to_the_table = info_table.google_table.link_table.link_to_the_table
        table_settings = info_table.google_table.link_table.column_settings
        return {"table_id": table_id,
                "group_id": group_id,
                "link_to_the_table": link_to_the_table, 
                "column_user_name": table_settings.user_name.availability, 
                "column_user_name_initial_word": table_settings.user_name.initial_word.word, 
                "column_user_last_name": table_settings.user_last_name.availability, 
                "column_user_last_name_initial_word": table_settings.user_last_name.initial_word.word, 
                "column_user_reference": table_settings.user_reference.availability, 
                "column_user_reference_initial_word": table_settings.user_reference.initial_word.word, 
                "column_user_group": table_settings.user_group.availability, 
                "column_user_group_initial_word": table_settings.user_group.initial_word.word, 
                "column_user_name_cabinet": table_settings.user_name_cabinet.availability, 
                "column_user_name_cabinet_initial_word": table_settings.user_name_cabinet.initial_word.word, 
                "column_headings": table_settings.headings.availability, 
                "column_headings_initial_word": table_settings.headings.initial_word.word, 
                "column_stop_content": table_settings.stop_content.availability, 
                "column_stop_content_initial_word": table_settings.stop_content.initial_word.word, 
                "column_ad_text": table_settings.ad_text.availability, 
                "column_ad_text_initial_word": table_settings.ad_text.initial_word.word, 
                "column_ad_media": table_settings.ad_media.availability, 
                "column_ad_media_initial_word": table_settings.ad_media.initial_word.word, 
                "column_target_audience": table_settings.target_audience.availability, 
                "column_target_audience_initial_word": table_settings.target_audience.initial_word.word, 
                "column_request_stop": table_settings.request_stop.availability, 
                "column_request_stop_initial_word": table_settings.request_stop.initial_word.word,
                "column_launch_status": table_settings.launch_status.availability, 
                "column_launch_status_initial_word": table_settings.launch_status.initial_word.word,
                "column_tasks": table_settings.tasks.availability, 
                "column_tasks_initial_word": table_settings.tasks.initial_word.word,
                "column_number_of_tasks": table_settings.number_of_tasks.number_of_tasks}
    else:
        return {"table_id": None,
                "group_id": None,
                "link_to_the_table": None, 
                "column_user_name": None, 
                "column_user_name_initial_word": None, 
                "column_user_last_name": None, 
                "column_user_last_name_initial_word": None, 
                "column_user_reference": None, 
                "column_user_reference_initial_word": None, 
                "column_user_group": None, 
                "column_user_group_initial_word": None, 
                "column_user_name_cabinet": None, 
                "column_user_name_cabinet_initial_word": None, 
                "column_headings": None, 
                "column_headings_initial_word": None, 
                "column_stop_content": None, 
                "column_stop_content_initial_word": None, 
                "column_ad_text": None, 
                "column_ad_text_initial_word": None, 
                "column_ad_media": None, 
                "column_ad_media_initial_word": None, 
                "column_target_audience": None, 
                "column_target_audience_initial_word": None, 
                "column_request_stop": None, 
                "column_request_stop_initial_word": None,
                "column_launch_status": None, 
                "column_launch_status_initial_word": None,
                "column_tasks": None, 
                "column_tasks_initial_word": None,
                "column_number_of_tasks": 0}

async def loading_curator_group_data(group_id: int) -> list:
    curated_groups = list_of_user_groups.query.filter_by(user_id=current_user.id).all()
    list_groups_user = [marathon_groups.query.filter_by(id=group.group_id).first().group_id for group in curated_groups]
    if int(group_id) not in list_groups_user:
        flash('Вы не курируете данную группу, доступ запрещён.', 'error')
        return []
    group_data = await loading_group_data(int(group_id))
    group_posts = await loading_group_posts(int(group_id))
    table_settings = await loading_group_table_settings(int(group_id))
    google_table = await loading_the_grid_linked_group_table(int(group_id))
    return [group_data, group_posts, table_settings, google_table]

def checking_access_rights_to_the_panel(rights_level: int) -> bool:
    """
    Проверка на наличие у текущего пользователя необходимого уровня доступа в панели.
    Параметр rights_level - положительное число, не меньше 1.
    Возвращает:
        True - если необходимые права есть
        False - если необходимых прав нет
    """
    if current_user.access_panel is None:
        return False
    if current_user.access_panel.access_id <= rights_level:
        return True
    else:
        return False

async def loading_list_of_users_with_rights() -> list:
    """Загрузка пользователей с правами, и сопоставление пользователя с правами"""
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас недостаточно прав для просмотра списка пользователей с правами.', 'error')
        return []
    list_users = db.session.query(User).join(user_access_rights_in_the_panel).all()
    try:
        data_users_in_vk = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str([user.vk_id for user in list_users]).replace('[', '').replace(']', ''), 'fields': 'photo_200'}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки данных пользователей с правами, повторите попытку чуть позже.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка, проблема со стороны ВК.', 'error')
        return []
    json_data_users = {}
    for user in data_users_in_vk:
        json_data_users.update({user['id']: {'first_name': user["first_name"], 'last_name': user["last_name"], 'photo_200': user["photo_200"]}})
    access_rights_data = []
    for user in list_users:
        access_rights_data.append(json.loads(str({"user_id": user.id, "vk_id": user.vk_id, "access_name": user.access_panel.access.access_name, "first_name": json_data_users.get(user.vk_id)['first_name'], "last_name": json_data_users.get(user.vk_id)['last_name'], "photo_200": json_data_users.get(user.vk_id)['photo_200'], "last_seen": datetime.fromtimestamp(user.last_seen).strftime("%d-%m-%Y, %H:%M:%S")}).replace("'", '"')))
    return access_rights_data

def check_user_in_database(user_id: int):
    """Проверка, находится ли пользователь в базе, если нет - добавление в базу"""
    user_check = User.query.filter_by(vk_id=int(user_id)).first()
    if user_check is None:
        user = User(vk_id=int(user_id))
        db.session.add(user)
        db.session.commit()
        info_user = User.query.filter_by(vk_id=int(user_id)).first()
        return info_user.id
    user_check = User.query.filter_by(vk_id=int(user_id)).first()
    if user_check is not None:
        return user_check.id
    return

def granting_rights_in_the_panel(access_name: str, user_id: int) -> None:
    """Выдача прав пользователю в панели управления"""
    if checking_access_rights_to_the_panel(3) is False:
        flash('У Вас не хватает прав для изменения.', 'error')
        return
    info_access_rights = panel_access_rights.query.filter_by(access_name=access_name).first()
    if info_access_rights is None:
        flash('Выбранный тип прав несуществует, проверьте корректность данных.', 'error')
        return
    
    info_user = User.query.filter_by(id=user_id).first()
    try:
        data_user = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': info_user.vk_id, 'fields': 'photo_200', 'name_case': 'gen'}, timeout=10).json()['response'][0]
    except Timeout:
        flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
        return abort(400)
    except KeyError:
        flash('Произошла ошибка валидации данных аккаунта, сообщите об этом администрации.', 'error')
        return abort(400)
    if current_user.access_panel is None or current_user.access_panel.access_id > info_access_rights.id:
        flash('У Вас не хватает доступа для изменения.', 'error')
        return
    if current_user.id == user_id:
        flash('Невозможно изменить права самому себе.', 'error')
        return
    info_user_access = user_access_rights_in_the_panel.query.filter_by(user_id=user_id).first()
    if info_user_access is not None:
        if info_user_access.access_id is not None:
            if current_user.access_panel.access_id >= info_user_access.access_id:
                flash('Невозможно изменить права пользователю который выше или равен Вам по правам.', 'error')
                return
    if info_user_access is None:
        user = user_access_rights_in_the_panel(access_id=info_access_rights.id, user_id=user_id)
        db.session.add(user)
        db.session.commit()
        flash(f'«{data_user.get("first_name")} {data_user.get("last_name")}» успешно выданы права.', 'info')
    elif info_user_access.access_id != info_access_rights.id:
        info_user_access.access_id = info_access_rights.id
        db.session.add(info_user_access)
        db.session.commit()
        flash(f'«{data_user.get("first_name")} {data_user.get("last_name")}» успешно выданы права.', 'info')
    else:
        flash(f'У «{data_user.get("first_name")} {data_user.get("last_name")}» уже есть данные права.', 'error')
        return
    return

def revocation_of_rights_in_the_panel(user_id: int) -> None:
    """Отзыв прав к панели у пользователя"""
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает прав для отзыва.', 'error')
        return
    info_user = User.query.filter_by(id=user_id).first()
    try:
        data_user = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': info_user.vk_id, 'fields': 'photo_200', 'name_case': 'gen'}, timeout=10).json()['response'][0]
    except Timeout:
        flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
        return abort(400)
    except KeyError:
        flash('Произошла ошибка валидации данных аккаунта, сообщите об этом администрации.', 'error')
        return abort(400)
    
    if current_user.access_panel is None or current_user.access_panel.access is None or current_user.access_panel.access.id is None:
        flash('У Вас не хватает доступа для отзыва прав.', 'error')
        return
    if current_user.id == user_id:
        flash('Невозможно изменить права самому себе.', 'error')
        return
    info_user = User.query.filter_by(id=user_id).first()
    if info_user.access_panel is not None and info_user.access_panel.access is not None and info_user.access_panel.access.id is not None:
        if current_user.access_panel.access.id < info_user.access_panel.access.id and info_user.access_panel.access_id != 5:
            info_user.access_panel.access_id = 5
            db.session.add(info_user)
            db.session.commit()
            flash(f'Права у «{data_user.get("first_name")} {data_user.get("last_name")}» успешно отозваны.', 'info')
            return
        else:
            if info_user.access_panel.access_id == 5:
                flash(f'У «{data_user.get("first_name")} {data_user.get("last_name")}» уже минимальные права, отзыв невозможен.', 'error')
                return
            else:
                flash(f'У Вас не хватает доступа чтобы отозвать права у «{data_user.get("first_name")} {data_user.get("last_name")}».', 'error')
                return
    else:
        flash(f'Права «{data_user.get("first_name")} {data_user.get("last_name")}» ранее не выдавались, отзыв невозможен.', 'error')
        return
    return

async def list_users_with_access_to_the_panel(issued: bool = True, requested: bool = False) -> list:
    if issued is True and requested is False:
        info_users = users_with_access_to_the_panel.query.filter_by(access='Выдан').all()
    elif requested is True:
        info_users = users_with_access_to_the_panel.query.filter_by(access='Запрошен').all()
        
    if info_users == [] and requested is not True:
        flash('Пользователи с выданым доступом к панели не обнаружены, повторите попытку позже.', 'error')
        return []
    elif info_users == [] and requested is True:
        flash('Пользователи с запрошенным доступом к панели не обнаружены, повторите попытку позже.', 'error')
        return []
    
    try:
        data_users_in_vk = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str([user.vk_id for user in info_users]).replace('[', '').replace(']', ''), 'fields': 'photo_200'}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки данных пользователей с доступом к панели, повторите попытку чуть позже.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка, проблема со стороны ВК.', 'error')
        return []
    
    dict_data_users = {}
    for user in data_users_in_vk:
        dict_data_users.update({user['id']: {'first_name': user["first_name"], 'last_name': user["last_name"], 'photo_200': user["photo_200"], 'vk_link': f'https://vk.com/id{user["id"]}'}})
    list_users = []
    for user in info_users:
        list_users.append({'id': user.vk_id, 
                           'first_name': dict_data_users.get(user.vk_id)["first_name"], 
                           'last_name': dict_data_users.get(user.vk_id)["last_name"], 
                           'photo_200': dict_data_users.get(user.vk_id)["photo_200"], 
                           'vk_link': dict_data_users.get(user.vk_id)["vk_link"]
                           })
    return list_users

async def removing_user_access_to_the_panel(vk_user_link: int) -> None:
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает доступа для отзыва доступа к панели.', 'error')
        return
    try:
        data_user = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str(vk_user_link).replace('https://m.vk.com/id', '').replace('https://m.vk.com/', '').replace('https://vk.com/id', '').replace('https://vk.com/', '')}, timeout=10).json()['response'][0]
    except Timeout:
        flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
        return
    except KeyError:
        flash('Произошла ошибка валидации данных аккаунта, сообщите об этом администрации.', 'error')
        return
    user_id = data_user['id']
    first_name = data_user['first_name']
    last_name = data_user['last_name']
    info_access = users_with_access_to_the_panel.query.filter_by(vk_id=user_id).first()
    if info_access is None:
        flash(f'У пользователя «{first_name} {last_name}» нет доступа к панели.', 'error')
        return
    db.session.delete(info_access)
    db.session.commit()
    flash(f'У пользователя «{first_name} {last_name}» отозван доступ к панели.', 'info')
    return

async def granting_the_user_access_to_the_panel(vk_user_link: int) -> None:
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает доступа для выдачи доступа к панели.', 'error')
        return
    try:
        data_user = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str(vk_user_link).replace('https://m.vk.com/id', '').replace('https://m.vk.com/', '').replace('https://vk.com/id', '').replace('https://vk.com/', '')}, timeout=10).json()['response'][0]
    except Timeout:
        flash('Произошла ошибка, превышено время ожидания ответа от сервера, повторите попытку позже.', 'error')
        return
    except KeyError:
        flash('Произошла ошибка валидации данных аккаунта, сообщите об этом администрации.', 'error')
        return
    user_id = data_user['id']
    first_name = data_user['first_name']
    last_name = data_user['last_name']
    info_access = users_with_access_to_the_panel.query.filter_by(vk_id=user_id).first()
    if info_access is not None and info_access.access == 'Выдан':
        flash(f'У пользователя «{first_name} {last_name}» уже есть доступ к панели.', 'error')
        return
    elif info_access is not None:
        info_access.access = 'Выдан'
        db.session.add(info_access)
        db.session.commit()
    else:
        user = users_with_access_to_the_panel(vk_id=user_id, access='Выдан')
        db.session.add(user)
        db.session.commit()
    flash(f'Пользователю «{first_name} {last_name}» выдан доступ к панели управления.', 'info')
    return

async def event_handling_new_post(group_id: int, request: dict) -> None:
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is None:
        return 
    info_post = posts_in_groups.query.filter_by(group_id=info_group.id, post_id=int(request['id'])).first()
    if info_post is None:
        post = posts_in_groups(group_id=info_group.id, post_id=int(request['id']))
        db.session.add(post)
        db.session.commit()
    return

def add_marathon_group(group_id: int, group_name: str) -> None:
    """Добавление группы марафона в базу"""
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает доступа для добавления группы марафона.', 'error')
        return
    name_environment_group = f'group_{group_id}'
    if os.environ.get(name_environment_group, None) is None:
        with open('.env', 'r+') as file:
            file.write(f'\n{name_environment_group}="{request.form.get("token_group")}"')
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is None:
        #server_title - название Callback сервера, 
        # который будет установлен в группу марафона макс. длинна 14 симв.
        #server_secret_key - секретный ключ, необходимый для проверки подлинности запрос 
        # и сервера присылающего события из группымакс длинна 50 симв.
        server_url, server_title, server_secret_key = f'{app.config["CALLBACK_SERVER_URL"]}{group_id}', f'{app.config["CALLBACK_SERVER_TITLE"]}', ''

        try:
            callback_api_vk = requests.post('https://api.vk.com/method/groups.addCallbackServer?access_token={}&v=5.131'.format(os.environ.get(name_environment_group)), data={'group_id': int(group_id), 'url': server_url, 'title': server_title, 'secret_key': server_secret_key}, timeout=10).json()['response']
        except Timeout:
            flash('Произошла ошибка при добавлении сервера API в группу, истекло время ожидания ответа от VK.', 'error')
            return
        except KeyError:
            flash(f'Произошла ошибка при добавлении сервера API в группу, проверьте что у токена группы есть все права.', 'error')
            return

        try:
            data_group = requests.post('https://api.vk.com/method/groups.join?access_token={}&v=5.131'.format(app.config['DUTY_VK_TOKEN']), data={'group_id': int(group_id)}, timeout=10).json()
        except Timeout:
            flash('Произошла ошибка при добавлении группы марафона, истекло время ожидания ответа от VK.', 'error')
            return
        except KeyError:
            flash(f'Произошла ошибка при добавлении группы марафона, проверьте, приглашён ли страничный бот в группу марафона.', 'error')
            return
        if data_group.get('error', None) is not None:
            flash(f'Произошла ошибка при добавлении группы марафона, проверьте, приглашён ли страничный бот в группу марафона.', 'error')
            return
        db_group = marathon_groups(group_id=group_id)
        db.session.add(db_group)
        db.session.commit()
        info_group = marathon_groups.query.filter_by(group_id=group_id).first()
        db_group_name = names_of_marathon_groups(name=group_name, group_id=info_group.id)
        db_group_environment = name_of_environment_variable_of_marathon_groups(name=name_environment_group, group_id=info_group.id)
        db_user_add_group = users_who_have_add_marathon_groups(user_id=current_user.id, group_id=info_group.id, time_of_addition=int(round(time.time())))
        db_callback_server = group_server_callback_api_data(server_id=int(callback_api_vk['server_id']), url=server_url, title=server_title, secret_key=server_secret_key, group_id=info_group.id)
        db.session.add_all([db_group_name, db_group_environment, db_user_add_group, db_callback_server])
        db.session.commit()
    else:
        flash(f'Группа «{group_name}» уже была ранее добавлена, повторное добавление не требуется.', 'error')
        return
    flash(f'Группа «{group_name}» успешно добавлена.', 'info')
    return

async def edit_callback_server_settings_in_group(group_id: int, settings: dict = app.config['CALLBACK_SERVER_SETTINGS']) -> None:
    name_environment_group = f'group_{group_id}'
    if os.environ.get(name_environment_group, None) is None:
        flash('При изменении настроек Callback сервера произошла ошибка, не найден токен группы.', 'error')
        return
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is None:
        flash('При изменении настроек Callback сервера произошла ошибка, группа марафона не обнаружена, возможно она была удалена.', 'error')
        return
    elif info_group.callback_server is None:
        flash('При изменении настроек Callback сервера произошла ошибка, не обнаружены данные сервера.', 'error')
        return
    
    settings.update({'group_id': group_id, 'server_id': info_group.callback_server.server_id})
    
    try:
        callback_api_vk = requests.post('https://api.vk.com/method/groups.setCallbackSettings?access_token={}&v=5.131'.format(os.environ.get(name_environment_group)), data=settings, timeout=10).json()['response']
    except Timeout:
        flash('При изменении настроек Callback сервера произошла ошибка, истекло время ожидания ответа от VK.', 'error')
        return
    except KeyError:
        flash(f'При изменении настроек Callback сервера произошла ошибка, проверьте что у токена группы есть все права.', 'error')
        return
    return callback_api_vk

async def loading_list_of_marathon_groups() -> list:
    """Загрузка общего списка групп марафонов(без связки с ними кураторов)"""
    list_marathon_groups = db.session.query(marathon_groups).options(joinedload(marathon_groups.name_group), joinedload(marathon_groups.name_environment), joinedload(marathon_groups.google_table), joinedload(marathon_groups.user_who_added)).all()
    list_groups = [group for group in list_marathon_groups]
    try:
        data_users_in_vk = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str([group.user_who_added.user.vk_id for group in list_marathon_groups]).replace('[', '').replace(']', ''), 'fields': 'photo_200'}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки данных пользователей добавивших группы марафонов, истекло время ожидания ответа от серверов ВК, повторите попытку чуть позже.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка, проблема со стороны ВК.', 'error')
        return []
    json_users_data = {}
    for user in data_users_in_vk:
        json_users_data.update({user['id']: {'first_name': user["first_name"], 'last_name': user["last_name"], 'photo_200': user["photo_200"]}})
    ready_list_of_marathon_groups = []
    for group in list_groups:
        try:
            data_marathon_group = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(os.environ.get(group.name_environment.name)), timeout=10).json()['response'][0]
        except Timeout:
            flash('Произошла ошибка загрузки данных о группах марафонов, истекло время ожидания ответа от серверов ВК, повторите попытку чуть позже.', 'error')
            return []
        except KeyError:
            flash('Произошла ошибка при получении данных о группах марафонов, проблема со стороны ВК.', 'error')
            return []
        except IndexError:
            flash(f'Произошла ошибка, при получении данных о группах марафонов, проблема либо со стороны ВК, либо токен группы «{group.name_group.name}» недействителен.', 'error')
            return []
        if str(data_marathon_group['name']) != str(group.name_group.name):
            info_group_name = names_of_marathon_groups.query.filter_by(group_id=group.id).one()
            info_group_name.name = str(data_marathon_group['name'])
            db.session.add(info_group_name)
            db.session.commit()
        ready_list_of_marathon_groups.append(json.loads(str({"id": group.id, "group_id": group.group_id, "name": group.name_group.name if str(data_marathon_group['name']) == str(group.name_group.name) else data_marathon_group['name'], "photo_group_200": data_marathon_group.get("photo_200", None), "environment": group.name_environment.name, "who_added_group_id": group.user_who_added.user.id, "who_added_group_vk_id": group.user_who_added.user.vk_id, "who_added_group_first_name": json_users_data.get(group.user_who_added.user.vk_id)['first_name'], "who_added_group_last_name": json_users_data.get(group.user_who_added.user.vk_id)['last_name'], "who_added_group_photo_200": json_users_data.get(group.user_who_added.user.vk_id)['photo_200'], "google_table": [{"id": group.google_table.link_table.id, "link": group.google_table.link_table.link_to_the_table, "time_of_addition": datetime.fromtimestamp(group.google_table.link_table.time_of_addition).strftime('%d-%m-%Y, %H:%M:%S')}] if group.google_table != [] else [], "time_of_addition_group": datetime.fromtimestamp(group.user_who_added.time_of_addition).strftime('%d-%m-%Y, %H:%M:%S')}).replace("'", '"')))
    return ready_list_of_marathon_groups

async def loading_marathon_group_settings(group_id: int) -> dict:
    """
    Возвращает словарь с настройками группы и их статусами
    """
    if checking_access_rights_to_the_panel(2) is not True:
        flash('У Вас не хватает доступа для просмотра настроек группы.', 'error')
        return {}
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is not None:
        if info_group.settings is None:
            info_settings = marathon_group_settings(group_id=info_group.id)
            db.session.add(info_settings)
            db.session.commit()
            info_group = marathon_groups.query.filter_by(group_id=group_id).first()
        return {'id': info_group.id, 
                'group_id': info_group.group_id, 
                'group_settings': {
                    'sheet_name': info_group.settings.name_sheet.name if info_group.settings.name_sheet is not None else None
                }}
    else:
        flash('Группа не обнаружена, возможно она была удалена.', 'error')
        return {}

async def edit_marathon_group_settings(group_id: int) -> None:
    """
    Позволяет редактировать настройки группы марафона.
    group_id - положительное число, не ID группы в базе.
    """
    if checking_access_rights_to_the_panel(2) is not True:
        flash('У Вас не хватает доступа для редактирования настроек группы.', 'error')
        return {}
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is None:
        flash('Группа не обнаружена, возможно она была удалена.', 'error')
        return
    if info_group.settings is None:
        flash('Произошла ошибка, настройки группы не обнаружены, повторите попытку позже.', 'error')
        return
    if request.form.get('sheet_name', None) is not None:
        if info_group.settings.name_sheet is None:
            info_settings = name_of_the_marathon_group_table_sheet(name=str(request.form.get('sheet_name')), setting_id=info_group.settings.id)
            db.session.add(info_settings)
            db.session.commit()
        if request.form.get('sheet_name') != info_group.settings.name_sheet.name:
            info_group.settings.name_sheet.name = str(request.form.get('sheet_name'))
            db.session.add(info_group)
            db.session.commit()
    else:
        flash('Произошла ошибка, не найдено название листа в таблице, обновите страницу и попробуйте снова.', 'error')
        return
    return

def delete_marathon_group(group_id: int) -> None:
    """Удаление группы марафона из базы"""
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает прав для удаление группы марафона.', 'error')
        return
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is not None:
        name_group = info_group.name_group.name
        info_names_group = names_of_marathon_groups.query.filter_by(group_id=info_group.id).first()
        info_name_of_environment_group = name_of_environment_variable_of_marathon_groups.query.filter_by(group_id=info_group.id).first()
        info_who_have_add_group = users_who_have_add_marathon_groups.query.filter_by(group_id=info_group.id).first()
        db.session.delete(info_group)
        db.session.delete(info_names_group)
        db.session.delete(info_name_of_environment_group)
        db.session.delete(info_who_have_add_group)
        db.session.commit()
    else:
        flash('Группа не обнаружена, возможно её ранее не добавляли, либо удалили раньше.', 'error')
        return
    flash(f'Группа «{name_group}» успешно удалена.', 'info')
    return

async def loading_list_curators_in_marathon_groups():
    """Загрузка списка групп марафонов, и распределённых по ним кураторов"""
    list_marathon_groups = db.session.query(marathon_groups).options(joinedload(marathon_groups.name_group), joinedload(marathon_groups.name_environment), joinedload(marathon_groups.curators_in_group)).all()
    list_groups = [group for group in list_marathon_groups]
    list_users = db.session.query(User).join(list_of_user_groups).all()
    try:
        data_users_in_vk = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str([user.vk_id for user in list_users]).replace('[', '').replace(']', ''), 'fields': 'photo_200'}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки данных кураторов в группах, повторите попытку чуть позже.', 'error')
        return []
    except KeyError:
        flash('Произошла ошибка, проблема со стороны ВК.', 'error')
        return []
    json_data_users = {}
    for user_vk, user in zip(data_users_in_vk, list_users):
        json_data_users.update({user.id: {'user_id': user_vk['id'], 'first_name': user_vk["first_name"], 'last_name': user_vk["last_name"], 'photo_200': user_vk["photo_200"]}})
    list_of_groups_and_curators = []
    for group in list_groups:
        data_marathon_group = []
        try:
            data_marathon_group = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(os.environ.get(group.name_environment.name)), timeout=10).json()['response'][0]
        except Timeout:
            flash('Произошла ошибка загрузки данных о группах марафонов при формировании списка кураторов в группах, истекло время ожидания ответа от серверов ВК, повторите попытку чуть позже.', 'error')
            return []
        except KeyError:
            flash('Произошла ошибка при получении данных о группах марафонов при формировании списка кураторов в группах, проблема со стороны ВК.', 'error')
            return []
        except IndexError:
            flash(f'Произошла ошибка, при получении данных о группах марафонов при формировании списка кураторов в группах, проблема либо со стороны ВК, либо токен группы «{group.name_group.name}» недействителен.', 'error')
            return []
        list_of_groups_and_curators.append(json.loads(str({"id": group.id, "group_id": data_marathon_group['id'], "name_group": data_marathon_group['name'], "photo_group_200": data_marathon_group['photo_200'], "curators_in_group": [{"curator_id": curator.id, "curator_vk_id": json_data_users.get(curator.id)['user_id'], "curator_first_name": json_data_users.get(curator.id)['first_name'], "curator_last_name": json_data_users.get(curator.id)['last_name'], "curator_photo_200": json_data_users.get(curator.id)['photo_200']} for curator in group.curators_in_group]}).replace("'", '"')))
    return list_of_groups_and_curators

async def loading_list_of_curators_to_add_to_group(group_id: int) -> dict:
    """
    Отдаёт словарь кураторов которых можно добавить в группу.
    Будут возвращены кураторы которые не состоят в данной группе.
    group_id - положительное число, ID группы VK, не ID в базе. 
    """
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is None:
        flash('Группа марафона не обнаружена, возможно она была удалена.', 'error')
        return [[], []]
    list_of_curators = User.query.where(User.id.notin_(db.session.query(list_of_user_groups.user_id).where(list_of_user_groups.group_id == info_group.id))).all()
    if list_of_curators == []:
        flash('Произошла ошибка формирования списка кураторов для добавления в группу, кураторов не добавленных в данную группу нет.', 'error')
        return [[], []]
    try:
        data_users_vk = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data={'user_ids': str([user.vk_id for user in list_of_curators]).replace('[', '').replace(']', ''), 'fields': 'photo_200'}, timeout=10).json()['response']
    except Timeout:
        flash('Произошла ошибка загрузки данных кураторов, повторите попытку чуть позже.', 'error')
        return [[], []]
    except KeyError:
        flash('Произошла ошибка, проблема со стороны ВК.', 'error')
        return [[], []]
    dict_data_users = {}
    for user in data_users_vk:
        dict_data_users.update({user['id']: {'user_id': user["id"], 'first_name': user["first_name"], 'last_name': user["last_name"], 'photo_200': user["photo_200"]}})
    list_curators = []
    for user in list_of_curators:
        list_curators.append({'id': user.id, 'user_id': dict_data_users.get(user.vk_id)['user_id'], 'first_name': dict_data_users.get(user.vk_id)['first_name'], 'last_name': dict_data_users.get(user.vk_id)['last_name'], 'photo_200': dict_data_users.get(user.vk_id)['photo_200']})
    return [list_curators, info_group.id]

def add_curator_to_group(curator_id: int, group_id: int) -> None:
    """
    Добавление кураторпа в группу марафона.
    curator_id - id куратора в базе (таблица User).
    group_id - id группы в базе (таблица marathon_groups).
    """
    if checking_access_rights_to_the_panel(3) is False:
        flash('У Вас не хватает доступа для добавления куратора в группу.', 'error')
        return
    info_group = marathon_groups.query.filter_by(id=group_id).first()
    if info_group is None:
        flash('Группа марафона не обнаружена, возможно она была удалена.', 'error')
        return
    info_curator = list_of_user_groups.query.filter_by(user_id=curator_id, group_id=group_id).first()
    if info_curator is not None:
        flash(f'Куратор уже курирует группу «{info_group.name_group.name}», выберите другого куратора.', 'error')
        return
    if info_curator is None:
        add_curator = list_of_user_groups(group_id=group_id, user_id=curator_id)
        db.session.add(add_curator)
        db.session.commit()
    flash(f'Куратор успешно добавлен в кураторство группы «{info_group.name_group.name}».', 'info')
    return

def removing_curator_from_marathon_group(curator_id: int, group_id: int) -> None:
    """Удаление куратора из группы марафона"""
    if checking_access_rights_to_the_panel(3) is False:
        flash('У Вас не хватает доступа для удаления куратора из группы марафона.', 'error')
        return
    info_group = marathon_groups.query.filter_by(id=group_id).first()
    if info_group is None:
        flash('Группа марафона не обнаружена, возможно она была удалена.', 'error')
        return
    info_curator = list_of_user_groups.query.filter_by(user_id=curator_id, group_id=group_id).first()
    if info_curator is None:
        flash(f'Куратор в группе «{info_group.name_group.name}» не обнаружен, возможно он был удалён из неё ранее.', 'error')
        return
    if info_group is not None and info_curator is not None:
        info_access_in_group = access_rights_for_curators_in_groups.query.filter_by(group_id=group_id, user_id=curator_id).first()
        if info_access_in_group is not None:
            db.session.delete(info_access_in_group)
        db.session.delete(info_curator)
        db.session.commit()
    flash(f'Куратор успешно удалён из группы марафона «{info_group.name_group.name}».', 'info')
    return

def transfer_of_the_curator_from_group_to_group(curator_id: int, group_id: int, which_group_id: int) -> None:
    """Перевод куратора, из одной группы в другую"""
    if checking_access_rights_to_the_panel(3) is False:
        flash('У Вас не хватает доступа для перевода куратора в другую группу.', 'error')
        return
    #Поиск группы из которой будет перевод
    info_group = marathon_groups.query.filter_by(id=group_id).first()
    if info_group is None:
        flash('Группа марафона из которой будет перевод куратора не обнаружена, возможно она была удалена.', 'error')
        return
    #Проверка на присутствие куратора в группе из которой его переводят
    info_curator = list_of_user_groups.query.filter_by(user_id=curator_id, group_id=group_id).first()
    if info_curator is None:
        flash(f'Куратор в группе «{info_group.name_group.name}» не обнаружен, возможно он был удалён или переведён из неё ранее.', 'error')
        return
    #Поиск группы в которую будут переводить
    info_which_group = marathon_groups.query.filter_by(id=which_group_id).first()
    if info_which_group is None:
        flash('Группа марафона в которую будет перевод куратора не обнаружена, возможно она была удалена.', 'error')
        return
    #Проверка на отсутствие куратора в группе, в которую его переводят
    info_curator_two = list_of_user_groups.query.filter_by(user_id=curator_id, group_id=which_group_id).first()
    if info_curator_two is not None:
        flash('Куратор уже состоит в группе в которую должен быть перевод.', 'error')
        return
    which_group = list_of_user_groups(group_id=which_group_id, user_id=curator_id)
    #Удаляем куратора из группы из которой его переводят
    db.session.delete(info_curator)
    #Добавление куратора в группу, в которую его переводят
    db.session.add(which_group)
    #Удаление прав куратора в группе, из которой его переводят(будет в будущем)
    #Выдача прав куратору в группе, в которую его переводят(будет в будущем)
    db.session.commit()
    return

async def get_information_on_the_google_table(link: str, info_table=False, info_table_grid=False) -> json:
    SCOPES = app.config['SCOPES_GOOGLE']
    SPREADSHEET_ID = await shortening_google_links_to_spreadsheet_id(link)
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except:
            flash('Произошла ошибка валидности токена для взаимодействия с GOOGLE таблицами.', 'error')
            return
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                with open('token.json', 'r+') as file:
                    json_token = ast.literal_eval(file.read())
                    try:
                        data_google_token = requests.post('https://accounts.google.com/o/oauth2/token', data={'client_id': json_token.get('client_id'), 'client_secret': json_token.get('client_secret'), 'refresh_token': json_token.get('refresh_token'), 'grant_type': 'refresh_token'}, timeout=10).json()
                    except Timeout:
                        flash('Произошла ошибка, превышено время ожидания ответа от сервера Google, повторите попытку позже.', 'error')
                        return
                    if data_google_token.get('error', None) is not None and data_google_token.get('error') == 'invalid_grant':
                        flash('Произошла ошибка получения информации о таблице, токен для взаимодействия с таблицами недействителен.', 'error')
                        return
                    json_token['token'] = str(data_google_token['access_token'])
                    file.write(str(json_token))
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        if info_table is not False and info_table_grid is not False:
            response_data = sheet.get(spreadsheetId=SPREADSHEET_ID,
                                        ranges=[], includeGridData=True).execute()
        elif info_table is not False and info_table_grid is False:
            response_data = sheet.get(spreadsheetId=SPREADSHEET_ID,
                                        ranges=[], includeGridData=False).execute()
        return response_data
    except HttpError as err:
        flash('Произошла ошибка получения информации о таблице, повторите попытку позже.', 'error')
        return
    return

async def get_values_in_google_spreadsheet(spreadsheet: str, range: str, value_render_option: str = 'FORMATTED_VALUE', date_time_render_option: str = 'SERIAL_NUMBER') -> json:
    SCOPES = app.config['SCOPES_GOOGLE']
    spreadsheet_id = await shortening_google_links_to_spreadsheet_id(spreadsheet)
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds is None:
        flash('При получении значений страниц произошла ошибка, отсутствует параметр creds.', 'error')
        return []
    service = build('sheets', 'v4', credentials=creds)
    try:
        response = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option).execute()
    except TypeError as msg:
        flash(f'При получении значений таблицы, возникла ошибка «{msg}»', 'error')
        return []
    return response

async def values_update_in_google_spreadsheet(spreadsheet: str = "", range_name: str = "", value: str = "", value_input_option: str ="USER_ENTERED", majorDimension: str = "ROWS") -> None:
    if spreadsheet == "":
        flash('Невозможно изменить значение ячейки, не обнаружено ID таблицы.', 'error')
        return
    elif range_name == "":
        flash('Невозможно изменить значение ячейки, не передан координат ячейки.', 'error')
        return
    SCOPES = app.config['SCOPES_GOOGLE']
    spreadsheet_id = await shortening_google_links_to_spreadsheet_id(spreadsheet)
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds is None:
        flash('При обновлении значения произошла ошибка, отсутствует параметр creds.', 'error')
        return []
    try:

        service = build('sheets', 'v4', credentials=creds)
        values = [
            [value]
        ]
        body = {
            'majorDimension': majorDimension,
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        flash(f'Значение ячейки «{range_name}» было изменено на «{value}»', 'info')
    except HttpError as error:
        print(f"При изменении значения ячейки возникла ошибка: {error}")
        return
    return

async def edit_status_of_user_task(group_id: int, user_id: int, task_number: int, post_id: int, comment_id: int,  task_status: str = '') -> None:
    """
    Изменения статуса задания пользователя в таблице
    """
    if not group_id:
        flash('Произошла ошибка изменения статуса, ID группы пустой.', 'error')
        return
    elif not user_id:
        flash('Произошла ошибка изменения статуса, ID пользователя пустой.', 'error')
        return
    elif not task_number:
        flash('Произошла ошибка изменения статуса, ID задания пустой.', 'error')
        return
    elif not post_id:
        flash('Произошла ошибка изменения статуса, ID поста пустой.', 'error')
        return
    elif not comment_id:
        flash('Произошла ошибка изменения статуса, ID комментария пустой.', 'error')
        return
    elif not task_status:
        flash('Произошла ошибка изменения статуса, статус задание пустой.', 'error')
        return
    
    info_group = db.session.query(marathon_groups).filter(marathon_groups.id == group_id).options(joinedload(marathon_groups.google_table)).first()

    if info_group is None:
        flash('Произошла ошибка, группа марафона не обнаружена, возможно она была удалена.', 'error')
        return
    elif info_group.google_table is None or info_group.google_table.link_table is None:
        flash('Произошла ошибка, к группе не привязана таблица, возможно она была удалена.', 'error')
        return
    
    if info_group.settings is not None:
        if info_group.settings.name_sheet is not None and not str(info_group.settings.name_sheet.name):
            coordinates = await search_for_user_coordinates_in_the_table(info_group.group_id, info_group.google_table.link_table.link_to_the_table, user_id, str(info_group.settings.name_sheet.name))
        else:
            coordinates = await search_for_user_coordinates_in_the_table(info_group.group_id, info_group.google_table.link_table.link_to_the_table, user_id)
    else:
        coordinates = await search_for_user_coordinates_in_the_table(info_group.group_id, info_group.google_table.link_table.link_to_the_table, user_id)

    if coordinates == {}:
        flash(f'Произошла ошибка изменения статуса, задание с номером «{task_number}» не было изменено.', 'error')
        return

    if coordinates.get(f'tasks_{task_number}', None) is None:
        flash(f'Произошла ошибка изменения статуса, задание с номером «{task_number}» не обнаружено в таблице.', 'error')
        return
    
    await values_update_in_google_spreadsheet(info_group.google_table.link_table.link_to_the_table, f'{coordinates.get("page")}!{coordinates.get(f"tasks_{task_number}")}{coordinates.get("user_row")}', task_status)
    info_member = db.session.query(marathon_users).filter_by(group_id=info_group.id, vk_id=user_id).first()
    if info_member is not None:
        info_task = db.session.query(status_of_marathon_users_tasks).filter_by(user_id=info_member.id, group_id=info_group.id, task_number=task_number).first()
        if info_task is not None:
            info_task.task_status = task_status
            db.session.add(info_task)
            db.session.commit()
            info_post = db.session.query(information_about_the_post_with_the_task).filter_by(user_id=info_member.id, task_id=info_task.id).first()
            if info_post is None:
                post = information_about_the_post_with_the_task(post_id=post_id, comment_id=comment_id, user_id=info_member.id, task_id=info_task.id)
                db.session.add(post)
                db.session.commit()
        else:
            task = status_of_marathon_users_tasks(task_number=task_number, task_status=task_status, user_id=info_member.id, group_id=info_group.id)
            db.session.add(task)
            db.session.commit()
            info_task = db.session.query(status_of_marathon_users_tasks).filter_by(user_id=info_member.id, group_id=info_group.id, task_number=task_number).first()
            info_post = db.session.query(information_about_the_post_with_the_task).filter_by(user_id=info_member.id, task_id=info_task.id).first()
            if info_post is None:
                post = information_about_the_post_with_the_task(post_id=post_id, comment_id=comment_id, user_id=info_member.id, task_id=info_task.id)
                db.session.add(post)
                db.session.commit()
    else:
        group_member = marathon_users(vk_id=user_id, group_id=info_group.id)
        db.session.add(group_member)
        db.session.commit()
        info_member = db.session.query(marathon_users).filter_by(group_id=info_group.id, vk_id=user_id).first()
        info_task = db.session.query(status_of_marathon_users_tasks).filter_by(user_id=info_member.id, group_id=info_group.id, task_number=task_number).first()
        if info_task is not None:
            info_task.task_status = task_status
            db.session.add(info_task)
            db.session.commit()
            info_post = db.session.query(information_about_the_post_with_the_task).filter_by(user_id=info_member.id, task_id=info_task.id).first()
            if info_post is None:
                post = information_about_the_post_with_the_task(post_id=post_id, comment_id=comment_id, user_id=info_member.id, task_id=info_task.id)
                db.session.add(post)
                db.session.commit()
        else:
            task = status_of_marathon_users_tasks(task_number=task_number, task_status=task_status, user_id=info_member.id, group_id=info_group.id)
            db.session.add(task)
            db.session.commit()
            info_task = db.session.query(status_of_marathon_users_tasks).filter_by(user_id=info_member.id, group_id=info_group.id, task_number=task_number).first()
            info_post = db.session.query(information_about_the_post_with_the_task).filter_by(user_id=info_member.id, task_id=info_task.id).first()
            if info_post is None:
                post = information_about_the_post_with_the_task(post_id=post_id, comment_id=comment_id, user_id=info_member.id, task_id=info_task.id)
                db.session.add(post)
                db.session.commit()
    return

async def search_for_user_coordinates_in_the_table(group_id: int, spreadsheet: str, user_id: int, page: str = '') -> dict:
    """
    Ищет строку с пользователем в указанной таблице и странице.
    """
    json_google_table = await get_information_on_the_google_table(spreadsheet, True)
    if json_google_table is None:
        flash('Произошла ошибка загрузки данных таблицы, не получилось получить данные таблицы.', 'error')
        return {}
    if json_google_table.get('sheets', None) is None:
        flash('У привязанной к группе таблицы отсутствуют страницы, поиск пользователя невозможен.', 'error')
        return {}
    data_list_google_page_in_table = {}
    for sheet in json_google_table.get('sheets'):
        data_list_google_page_in_table.update({sheet['properties']['title']: 
                                    {'sheetId': sheet['properties']['sheetId'], 
                                        'title': sheet['properties']['title'], 
                                        'index': sheet['properties']['index'], 
                                        'sheetType': sheet['properties']['sheetType'],
                                        'tabColorStyle': sheet['properties']['tabColorStyle'] if sheet['properties'].get('tabColorStyle', None) is not None else None, 
                                        'gridProperties': sheet['properties']['gridProperties']
                                        }
                                        })
    if not page:
        try:
            group_name_environment = f'group_{group_id}'
            data_response_group = requests.post('https://api.vk.com/method/groups.getById?access_token={}&v=5.131'.format(os.environ.get(group_name_environment)), data = {'group_id': group_id}, timeout=10).json()['response'][0]
        except Timeout:
            flash('Произошла ошибка, истекло время ожидания от сервера.', 'error')
            return {}
        except KeyError:
            flash('Произошла ошибка, проблема со стороны ВК.', 'error')
            return {}
        group_name = data_response_group['name']
        name_page = group_name.split()[0]
        for sheet in data_list_google_page_in_table.keys():
            if name_page in sheet:
                name_page = sheet
                break
        if not name_page:
            flash('Лист привязанный к группе не обнаружен, проверьте что в названии листа есть часть названия группы, или в настройках указано название листа.', 'error')
            return {}
        page = name_page
    #запрос данных о пользователе для поиска
    try:
        data_response_user = requests.post('https://api.vk.com/method/users.get?access_token={}&v=5.131'.format(app.config['VK_TOKEN']), data = {'user_ids': user_id, 'fields': 'domain'}, timeout=10).json()['response'][0]
    except Timeout:
        flash('Произошла ошибка получения данных о пользователе, истекло время ожидания от сервера.', 'error')
        return {}
    except KeyError:
        flash('Произошла ошибка получения данных о пользователе, проблема со стороны ВК.', 'error')
        return {}
    user_domain = data_response_user['domain']
    user_vk_id = str(data_response_user['id'])
    user_first_name = data_response_user['first_name']
    user_last_name = data_response_user['last_name']
    #получение значений всего листа
    page_values = await get_values_in_google_spreadsheet(spreadsheet, page, date_time_render_option='FORMATTED_STRING')
    if page_values.get('values', None) is None:
        flash('Произошла ошибка изменения статуса, в листе группы отсутствуют значения.', 'error')
        return {}
    elif data_list_google_page_in_table.get(page, None) is None:
        flash('Ошибка поиска пользователя в таблицe, у листа нет значений.', 'error')
        return {}
    alphabet = await forming_list_of_the_alphabet_of_the_table(data_list_google_page_in_table.get(page)['gridProperties']['columnCount'])
    row_index = -1
    current_iteration = 1
    for row in page_values['values']:
        for cell in row:
            if re.search(user_domain, cell) is not None or re.search(user_vk_id, cell) is not None or re.search(user_first_name, cell) is not None or re.search(user_last_name, cell) is not None:
                row_index = current_iteration
                break
        current_iteration += 1
    table_settings = await loading_group_table_settings(group_id)
    if row_index >= 0:
        json_data_column_name = {'user_row': row_index, 'page': page}
        number_of_tasks = 1
        for setting in table_settings:
            cell_index = 0
            if table_settings.get(setting) is True:
                for cell in page_values['values'][0]:
                    initial_word = str(table_settings.get(setting + '_initial_word')).replace('(', '\(').replace(')', '\)').replace('[', '\[').replace(']', '\]').replace('{', '\{').replace('}', '\}')
                    if re.search(initial_word, cell) is not None and setting != 'column_tasks':
                        word = alphabet[cell_index]
                        json_data_column_name.update({str(setting).replace('column_', ''): word})
                    elif re.search(initial_word, cell) is not None and setting == 'column_tasks':
                        word = alphabet[cell_index]
                        json_data_column_name.update({f'{str(setting).replace("column_", "")}_{number_of_tasks}': word})
                        number_of_tasks += 1
                    cell_index += 1
                    continue
    elif row_index < 0:
        values_to_add_to_the_table = []
        for cell in page_values['values'][0]:
            cell_index = 0
            value = ''
            if table_settings.get('column_user_name', False) is True:
                initial_word = str(table_settings.get('column_user_name_initial_word')).replace('(', '\(').replace(')', '\)').replace('[', '\[').replace(']', '\]').replace('{', '\{').replace('}', '\}')
                if re.search(initial_word, cell) is not None:
                    word = alphabet[cell_index]
                    value = user_first_name
            if table_settings.get('column_user_last_name', False) is True:
                initial_word = str(table_settings.get('column_user_last_name_initial_word')).replace('(', '\(').replace(')', '\)').replace('[', '\[').replace(']', '\]').replace('{', '\{').replace('}', '\}')
                if re.search(initial_word, cell) is not None:
                    word = alphabet[cell_index]
                    value = user_last_name
            if table_settings.get('column_user_reference', False) is True:
                initial_word = str(table_settings.get('column_user_reference_initial_word')).replace('(', '\(').replace(')', '\)').replace('[', '\[').replace(']', '\]').replace('{', '\{').replace('}', '\}')
                if re.search(initial_word, cell) is not None:
                    word = alphabet[cell_index]
                    value = f'https://vk.com/{user_domain}'
            values_to_add_to_the_table.append(value)
        await adding_row_to_table(spreadsheet, page, values_to_add_to_the_table)
        response = await search_for_user_coordinates_in_the_table(group_id, spreadsheet, user_id, page)
        return response
    return json_data_column_name

async def adding_row_to_table(spreadsheet: str, range: str, value: list = [], majorDimension: str = 'ROWS', valueInputOption: str = 'USER_ENTERED') -> None:
    """Добавление новой строки в лист таблицы"""
    if spreadsheet == "":
        flash('Невозможно добавить строку, не обнаружено ID таблицы.', 'error')
        return
    elif range == "":
        flash('Невозможно добавить строку, не переданы координаты ячеек.', 'error')
        return
    #Если не добавить !A1 - новая строка будет добавлена не с начальной колонки A, а с середины
    range = range + '!A1'
    SCOPES = app.config['SCOPES_GOOGLE']
    spreadsheet_id = await shortening_google_links_to_spreadsheet_id(spreadsheet)
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds is None:
        flash('При добавлении строки произошла ошибка, отсутствует параметр creds.', 'error')
        return
    try:

        service = build('sheets', 'v4', credentials=creds)
        values = [
            value
        ]
        body = {
            'majorDimension': majorDimension,
            'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range,
            valueInputOption=valueInputOption, body=body).execute()
        flash(f'Новая строка со значениями была добавлена в лист таблицы.', 'info')
    except HttpError as error:
        print(f"При добавлении строки в таблицу возникла ошибка: {error}")
        return
    return

async def shortening_google_links_to_spreadsheet_id(link: str) -> str:
    """Возвращает укороченную и валидную строку(для взаимодействия с таблицей) из ссылки на таблицу"""
    return str(link).replace('https://docs.google.com/spreadsheets/d/', '').replace('http://docs.google.com/spreadsheets/d/', '').replace('/edit?usp=sharing', '').replace('/edit#gid=0', '')

async def adding_google_tables(link: str) -> None:
    """Добавление Google таблицы в базу"""
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает доступа для добавления таблицы.', 'error')
        return
    info_table = google_marathon_tables.query.filter_by(link_to_the_table=link).first()
    if info_table is not None:
        flash('Ссылка на данную таблицу уже была ранее добавлена, повторное добавление не требуется.', 'error')
        return
    json_google_table = await get_information_on_the_google_table(link, True)
    table = google_marathon_tables(link_to_the_table=link, time_of_addition=int(round(time.time())))
    db.session.add(table)
    db.session.commit()
    info_table = google_marathon_tables.query.filter_by(link_to_the_table=link).first()
    if info_table.column_settings is None:
        column_settings = table_column_settings(table_id=info_table.id)
        db.session.add(column_settings)
        db.session.commit()
    info_column_settings = table_column_settings.query.filter_by(table_id=info_table.id).first()

    column_user_name = user_name_column_in_the_table(availability=bool(request.form.get('user_name_column', False)), setting_id=info_column_settings.id)
    column_last_name = user_last_name_column_in_the_table(availability=bool(request.form.get('user_last_name_column', False)), setting_id=info_column_settings.id)
    column_reference = user_reference_column_in_the_table(availability=bool(request.form.get('user_reference_name_column', False)), setting_id=info_column_settings.id)
    column_group = user_group_column_in_the_table(availability=bool(request.form.get('user_group_name_column', False)), setting_id=info_column_settings.id)
    column_name_cabinet = user_name_cabinet_column_in_the_table(availability=bool(request.form.get('user_name_cabinet_name_column', False)), setting_id=info_column_settings.id)
    column_headings = headings_column_in_the_table(availability=bool(request.form.get('headings_name_column', False)), setting_id=info_column_settings.id)
    column_stop_content = stop_content_column_in_the_table(availability=bool(request.form.get('stop_content_name_column', False)), setting_id=info_column_settings.id)
    column_ad_text = ad_text_column_in_the_table(availability=bool(request.form.get('ad_text_name_column', False)), setting_id=info_column_settings.id)
    column_ad_media = ad_media_column_in_the_table(availability=bool(request.form.get('ad_media_name_column', False)), setting_id=info_column_settings.id)
    column_target_audience = target_audience_column_in_the_table(availability=bool(request.form.get('target_audience_name_column', False)), setting_id=info_column_settings.id)
    column_request_stop = request_stop_column_in_the_table(availability=bool(request.form.get('request_stop_name_column', False)), setting_id=info_column_settings.id)
    column_launch_status = launch_status_column_in_the_table(availability=bool(request.form.get('launch_status_name_column', False)), setting_id=info_column_settings.id)
    column_tasks = tasks_column_in_the_table(availability=bool(request.form.get('tasks_name_column', False)), setting_id=info_column_settings.id)
    number_of_tasks = number_of_tasks_in_the_marathon_table(number_of_tasks=int(request.form.get('number_of_tasks', 0) if str(request.form.get('number_of_tasks', '')) != '' else 0), setting_id=info_column_settings.id)

    db.session.add_all([column_user_name, column_last_name, column_reference, column_group, column_name_cabinet, column_headings, column_stop_content, column_ad_text, column_ad_media, column_target_audience, column_request_stop, column_launch_status, column_tasks, number_of_tasks])
    db.session.commit()

    info_column_settings = table_column_settings.query.filter_by(table_id=info_table.id).first()

    initial_word_user_name = initial_word_user_name_column_in_the_table(word=str(request.form.get('name_user_name_column', '')), column_id=info_column_settings.user_name.id)
    initial_word_user_last_name = initial_word_user_last_name_column_in_the_table(word=str(request.form.get('name_user_last_name_column', '')), column_id=info_column_settings.user_last_name.id)
    initial_word_user_reference = initial_word_user_reference_column_in_the_table(word=str(request.form.get('name_user_reference_column', '')), column_id=info_column_settings.user_reference.id)
    initial_word_user_group = initial_word_user_group_column_in_the_table(word=str(request.form.get('name_user_group_column', '')), column_id=info_column_settings.user_group.id)
    initial_word_user_name_cabinet = initial_word_user_name_cabinet_column_in_the_table(word=str(request.form.get('name_name_cabinet_column', '')), column_id=info_column_settings.user_name_cabinet.id)
    initial_word_headings = initial_word_headings_column_in_the_table(word=str(request.form.get('name_headings_column', '')), column_id=info_column_settings.headings.id)
    initial_word_stop_content = initial_word_stop_content_column_in_the_table(word=str(request.form.get('name_stop_content_column', '')), column_id=info_column_settings.stop_content.id)
    initial_word_ad_text = initial_word_ad_text_column_in_the_table(word=str(request.form.get('name_ad_text_column', '')), column_id=info_column_settings.ad_text.id)
    initial_word_ad_media = initial_word_ad_media_column_in_the_table(word=str(request.form.get('name_ad_media_column', '')), column_id=info_column_settings.ad_media.id)
    initial_word_target_audience = initial_word_target_audience_column_in_the_table(word=str(request.form.get('name_target_audience_column', '')), column_id=info_column_settings.target_audience.id)
    initial_word_request_stop = initial_word_request_stop_column_in_the_table(word=str(request.form.get('name_request_stop_column', '')), column_id=info_column_settings.request_stop.id)
    initial_word_launch_status = initial_word_launch_status_column_in_the_table(word=str(request.form.get('name_launch_status_column', '')), column_id=info_column_settings.launch_status.id)
    initial_word_tasks = initial_word_tasks_column_in_the_table(word=str(request.form.get('name_tasks_column', '')), column_id=info_column_settings.tasks.id)
    db.session.add_all([initial_word_user_name, initial_word_user_last_name, initial_word_user_reference, initial_word_user_group, initial_word_user_name_cabinet, initial_word_headings, initial_word_stop_content, initial_word_ad_text, initial_word_ad_media, initial_word_target_audience, initial_word_request_stop, initial_word_launch_status, initial_word_tasks])
    db.session.commit()
    flash(f"Таблица «{json_google_table['properties']['title']}» успешно добавлена.", 'info')
    return

async def list_of_google_tables() -> list:
    """Загрузка общего списка таблиц в базе"""
    list_tables = db.session.query(google_marathon_tables).all()
    if list_tables == []:
        flash('Ошибка загрузки списка Google таблиц, таблицы не были добавлены.', 'error')
        return []
    data_tables = []
    for table in list_tables:
        json_google_table = await get_information_on_the_google_table(table.link_to_the_table, True)
        if json_google_table is None:
            return []
        data_tables.append(json.loads(str({"id": table.id, "name": json_google_table['properties']['title'], "link": table.link_to_the_table, "time_of_addition": datetime.fromtimestamp(table.time_of_addition).strftime('%d-%m-%Y, %H:%M:%S')}).replace("'", '"')))
    return data_tables

async def delete_google_tables(table_id: int) -> None:
    """Удаление Google таблицы из базы по её id в базе"""
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает доступа для удаления таблицы.', 'error')
        return
    info_table = google_marathon_tables.query.filter_by(id=table_id).first()
    if info_table is None:
        flash('Google таблица не обнаружена, возможно она была удалена ранее.', 'error')
        return
    info_table_linked = tables_linked_to_marathon_groups.query.filter_by(table_id=table_id).all()
    if info_table_linked != []:
        for group in info_table_linked:
            db.session.delete(group)
    db.session.delete(info_table)
    db.session.commit()
    flash('Google таблица успешно удалена.', 'info')
    return

async def linking_table_to_marathon_group(group_id: int, table_id: int) -> None:
    """
    Привязка/перепревязка Google таблицы к группе.
    Group_id - vk_id группы, НЕ id группы в базе.
    Table_id - id таблицы в базе.
    """
    if checking_access_rights_to_the_panel(2) is False:
        flash('У Вас не хватает доступа для привязки таблицы к группе.', 'error')
        return
    info_group = marathon_groups.query.filter_by(group_id=group_id).first()
    if info_group is not None:
        info_table = google_marathon_tables.query.filter_by(id=table_id).first()
        if info_table is not None:
            info_linked_table = tables_linked_to_marathon_groups.query.filter_by(group_id=info_group.id).first()
            if info_linked_table is not None:
                info_linked_table.table_id = info_table.id
                db.session.add(info_linked_table)
                db.session.commit()
                flash('Привязанная ранее таблица была отвязана, а новая таблица привязана.', 'info')
                return
            else:
                table = tables_linked_to_marathon_groups(table_id=info_table.id, group_id=info_group.id)
                db.session.add(table)
                db.session.commit()
                flash('Таблица успешно привязана к группе.', 'info')
                return
        else:
            flash('Google таблица не обнаружена, возможно она была ранее удалена.', 'error')
            return
    else:
        flash('Группа марафона не обнаружена, возможно она была ранее удалена.', 'error')
        return
    return