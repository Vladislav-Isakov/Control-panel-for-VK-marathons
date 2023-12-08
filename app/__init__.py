import logging
from logging.handlers import RotatingFileHandler
import os
#import sentry_sdk
from flask import Flask
#from sentry_sdk.integrations.flask import FlaskIntegration
from config import Config
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
import requests
from requests.exceptions import Timeout
import ast
from dotenv import load_dotenv

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///app.db', tablename='apscheduler_jobs')
}

executors = {
    'default': {'type': 'threadpool', 'max_workers': 10},
    'processpool': ProcessPoolExecutor(max_workers=1)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, 
                             job_defaults=job_defaults, timezone=utc)

def update_token_google():
    with open('token.json', 'r+') as file:
        json_token = ast.literal_eval(file.read())
        try:
            data_google_token = requests.post('https://accounts.google.com/o/oauth2/token', data={'client_id': json_token.get('client_id'), 'client_secret': json_token.get('client_secret'), 'refresh_token': json_token.get('refresh_token'), 'grant_type': 'refresh_token'}, timeout=10).json()
        except Timeout:
            return
        if data_google_token.get('error', None) is not None and data_google_token.get('error') == 'invalid_grant':
            return
        json_token['token'] = str(data_google_token['access_token'])
        file.write(str(json_token))

if scheduler.get_job('update_token_google') is None:
    scheduler.add_job(update_token_google, trigger='cron', day='*/3', jitter=60, id='update_token_google', jobstore='default', executor='default', replace_existing=True)

# scheduler.start()

# sentry_sdk.init(
#     dsn=app.config['SENTRY_SDK_DSN'],
#     integrations=[
#         FlaskIntegration(),
#     ],
#     release="0.1.1",

#     traces_sample_rate=1.0,
#         _experiments={
#       "profiles_sample_rate": 1.0,
#     },
# )

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(__name__)
app.config.from_object(Config)

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(app=app, metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate(app, db)
csfr = CSRFProtect(app)
csfr.init_app(app)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Авторизируйтесь чтобы получить доступ к разделу.'
# при публикации панели включить login.login_message_category = "info"
# при публикации панели включить login.session_protection = "strong"

if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/panel.log', maxBytes=60240,
                                    backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)

from app import routes, models, errors