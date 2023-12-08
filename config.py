import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'test'
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
#    SESSION_COOKIE_SECURE = True
#    REMEMBER_COOKIE_SECURE = True
#    SESSION_COOKIE_HTTPONLY = True # необязательно, т.к по умолчанию в сессии стоит True
#    REMEMBER_COOKIE_HTTPONLY = True
#    SESSION_COOKIE_SAMESITE="Lax"
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    VK_TOKEN = os.environ.get('vk_token_group')
    SCOPES_GOOGLE = ["https://www.googleapis.com/auth/spreadsheets"]
    DUTY_VK_TOKEN = os.environ.get('USER_PAGE_TOKEN')
    SENTRY_SDK_DSN = os.environ.get('SENTRY_SDK')
    CALLBACK_SERVER_URL = "/api/vk/callback_api/"
    CALLBACK_SERVER_TITLE = "Marathon Panel"
    CALLBACK_SERVER_SETTINGS = {'message_new': 0,
                                'message_reply': 0,
                                'message_allow': 0,
                                'message_edit': 0,
                                'message_deny': 0,
                                'message_typing_state': 0,
                                'photo_new': 0,
                                'audio_new': 0,
                                'video_new': 0,
                                'wall_reply_new': 1,
                                'wall_reply_edit': 1,
                                'wall_reply_delete': 1,
                                'wall_reply_restore': 1,
                                'wall_post_new': 1,
                                'wall_repost': 0,
                                'board_post_new': 0,
                                'board_post_edit': 0,
                                'board_post_restore': 0,
                                'board_post_delete': 0,
                                'photo_comment_new': 0,
                                'photo_comment_edit': 0,
                                'photo_comment_delete': 0,
                                'photo_comment_restore': 0,
                                'video_comment_new': 0,
                                'video_comment_edit': 0,
                                'video_comment_delete': 0,
                                'video_comment_restore': 0,
                                'market_comment_new': 0,
                                'market_comment_edit': 0,
                                'market_comment_delete': 0,
                                'market_comment_restore': 0,
                                'market_order_new': 0,
                                'market_order_edit': 0,
                                'poll_vote_new': 0,
                                'group_join': 0,
                                'group_leave': 0,
                                'group_change_settings': 0,
                                'group_change_photo': 0,
                                'group_officers_edit': 0,
                                'user_block': 0,
                                'user_unblock': 0,
                                'lead_forms_new': 0,
                                'like_add': 0,
                                'like_remove': 0,
                                'donut_subscription_create': 0,
                                'donut_subscription_prolonged': 0,
                                'donut_subscription_cancelled': 0,
                                'donut_subscription_price_changed': 0,
                                'donut_subscription_expired': 0,
                                'donut_money_withdraw': 0,
                                'donut_money_withdraw_error': 0,
                                'message_event': 0
                                }


# message_new
# checkbox

# Уведомления о новых сообщениях (0 — выключить, 1 — включить).

# message_reply
# checkbox

# Уведомления об исходящем сообщении (0 — выключить, 1 — включить).

# message_allow
# checkbox

# Уведомления о подписке на сообщения  (0 — выключить, 1 — включить).

# message_edit
# checkbox

# Уведомления о редактировании сообщения (0 — выключить, 1 — включить).

# message_deny
# checkbox

# Уведомления о запрете на сообщения (0 — выключить, 1 — включить).

# message_typing_state
# checkbox

# Уведомления о наборе текста сообщения (0 — выключить, 1 — включить).

# photo_new
# checkbox

# Уведомления о добавлении новой фотографии (0 — выключить, 1 — включить).

# audio_new
# checkbox

# Уведомления о добавлении новой аудиозаписи (0 — выключить, 1 — включить).

# video_new
# checkbox

# Уведомления о добавлении новой видеозаписи (0 — выключить, 1 — включить).

# wall_reply_new
# checkbox

# Уведомления о добавлении нового комментария на стене (0 — выключить, 1 — включить).

# wall_reply_edit
# checkbox

# Уведомления о редактировании комментария на стене (0 — выключить, 1 — включить).

# wall_reply_delete
# checkbox

# Уведомления об удалении комментария на стене (0 — выключить, 1 — включить).

# wall_reply_restore
# checkbox

# Уведомления о восстановлении комментария на стене (0 — выключить, 1 — включить).

# wall_post_new
# checkbox

# Уведомления о новой записи на стене (0 — выключить, 1 — включить).

# wall_repost
# checkbox

# Уведомления о репосте записи (0 — выключить, 1 — включить).

# board_post_new
# checkbox

# Уведомления о создании комментария в обсуждении (0 — выключить, 1 — включить).

# board_post_edit
# checkbox

# Уведомления о редактировании комментария в обсуждении (0 — выключить, 1 — включить).

# board_post_restore
# checkbox

# Уведомление о восстановлении комментария в обсуждении (0 — выключить, 1 — включить).

# board_post_delete
# checkbox

# Уведомления об удалении комментария в обсуждении (0 — выключить, 1 — включить).

# photo_comment_new
# checkbox

# Уведомления о добавлении нового комментария к фото (0 — выключить, 1 — включить).

# photo_comment_edit
# checkbox

# Уведомления о редактировании комментария к фото (0 — выключить, 1 — включить).

# photo_comment_delete
# checkbox

# Уведомления об удалении комментария к фото (0 — выключить, 1 — включить).

# photo_comment_restore
# checkbox

# Уведомления о восстановлении комментария к фото (0 — выключить, 1 — включить).

# video_comment_new
# checkbox

# Уведомления о добавлении нового комментария к видео (0 — выключить, 1 — включить).

# video_comment_edit
# checkbox

# Уведомления о редактировании комментария к видео (0 — выключить, 1 — включить).

# video_comment_delete
# checkbox

# Уведомления об удалении комментария к видео (0 — выключить, 1 — включить).

# video_comment_restore
# checkbox

# Уведомления о восстановлении комментария к видео (0 — выключить, 1 — включить).

# market_comment_new
# checkbox

# Уведомления о добавлении нового комментария к товару (0 — выключить, 1 — включить).

# market_comment_edit
# checkbox

# Уведомления о редактировании комментария к товару (0 — выключить, 1 — включить).

# market_comment_delete
# checkbox

# Уведомления об удалении комментария к товару (0 — выключить, 1 — включить).

# market_comment_restore
# checkbox

# Уведомления о восстановлении комментария к товару (0 — выключить, 1 — включить).

# market_order_new
# checkbox

# market_order_edit
# checkbox

# poll_vote_new
# checkbox

# Уведомления о новом голосе в публичных опросах (0 — выключить, 1 — включить).

# group_join
# checkbox

# Уведомления о вступлении в сообщество (0 — выключить, 1 — включить).

# group_leave
# checkbox

# Уведомления о выходе из сообщества (0 — выключить, 1 — включить).

# group_change_settings
# checkbox

# Уведомления об изменении настроек (0 — выключить, 1 — включить).

# group_change_photo
# checkbox

# Уведомления об изменении главной фотографии (0 — выключить, 1 — включить).

# group_officers_edit
# checkbox

# Уведомления об изменении руководства (0 — выключить, 1 — включить).

# user_block
# checkbox

# Уведомления об внесении пользователя в чёрный список (0 — выключить, 1 — включить).

# user_unblock
# checkbox

# Уведомления об исключении пользователя из чёрного списка (0 — выключить, 1 — включить).

# lead_forms_new
# checkbox

# Уведомления о заполнении формы.

# like_add
# checkbox

# Уведомления о новой отметке «Мне нравится» (0 — выключить, 1 — включить).

# like_remove
# checkbox

# Уведомления о снятии отметки «Мне нравится» (0 — выключить, 1 — включить).

# message_event
# checkbox

# donut_subscription_create
# checkbox

# Уведомление о создании подписки (0 — выключить, 1 — включить).

# donut_subscription_prolonged
# checkbox

# Уведомление о продлении подписки (0 — выключить, 1 — включить).

# donut_subscription_cancelled
# checkbox

# Уведомление об отмене подписки (0 — выключить, 1 — включить).

# donut_subscription_price_changed
# checkbox

# Уведомление об изменении стоимости подписки (0 — выключить, 1 — включить).

# donut_subscription_expired
# checkbox

# Уведомление о том, что подписка истекла (0 — выключить, 1 — включить).

# donut_money_withdraw
# checkbox

# Уведомление о выводе денег (0 — выключить, 1 — включить).

# donut_money_withdraw_error
# checkbox

# Уведомление об ошибке при выводе денег (0 — выключить, 1 — включить).