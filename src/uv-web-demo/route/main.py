import logging

from flask import Blueprint, render_template, session

from ..app_config import AppConfig
from ..db import DB
from ..util import login_required

main_bp = Blueprint('main', __name__)
app_logger = logging.getLogger(AppConfig.PROJECT_NAME + "." + __name__)


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    app_logger.debug(f'session user: {session.get("user")}')
    s_user = session.get("user")
    username = 'anonymous'
    if s_user:
        username = s_user.get('username')

    books = DB.query("SELECT * FROM t_book")
    app_logger.debug(f'{books=}')
    return render_template('index.html', username=username, books=books)


@main_bp.get('/dashboard')
@login_required
def dashboard():
    s_user = session.get("user")
    username = 'anonymous'
    if s_user:
        username = s_user.get('username')
    return render_template('dashboard.html', username=username)
