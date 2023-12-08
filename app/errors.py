from flask import render_template
from flask_login import current_user
from app import app, db

@app.errorhandler(Exception)
def found_error(error):
    app.logger.error('Возникла ошибка в контексте аккаунта пользователя с ID: %s', current_user.vk_id, exc_info=True)
    pass

@app.errorhandler(404)
def not_found_error_404(error):
    return render_template('errors/404_v2.html'), 404

@app.errorhandler(413)
def not_found_error_413(error):
    return render_template('errors/404_v1.html'), 404

@app.errorhandler(500)
def internal_error_500(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500