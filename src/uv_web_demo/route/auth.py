import logging

from flask import Blueprint, request, session, redirect, render_template, url_for

from ..app_config import AppConfig
from ..util import PasswordUtil
from ..db import DB

app_logger = logging.getLogger(AppConfig.PROJECT_NAME + "." + __name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    username = None
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db_user = DB.query(
            """
            SELECT a.username, a.password, a.salt
            FROM t_user as a
            WHERE a.username = ?;
            """,
            (username,)
        )
        app_logger.debug(f'db_user: {db_user}')

        if db_user:
            db_user = db_user[0]
            if PasswordUtil.verify_password(password, db_user.get('password'), db_user.get('salt')):
                session.permanent = True
                session['user'] = {'username': username}
                next_url = session.pop('next_url', None) or url_for('main.index')
                return redirect(next_url)
            else:
                error = '密码错误'
        else:
            error = f'该用户 {username}  不存在'

    return render_template('login.html', error=error, username=username)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if password != password_confirm:
            return render_template('register.html', error='两次密码不一致')

        # 检查用户是否已存在
        existing_user = DB.query(
            """
            SELECT username
            FROM t_user
            WHERE username = ?;
            """,
            (username,)
        )

        if existing_user:
            error = f'用户名 {username} 已存在'
        else:
            # 生成 salt 和 hash
            salt = PasswordUtil.generate_salt()
            password_hash = PasswordUtil.hash_password(password, salt)

            # 存储到数据库
            DB.execute(
                """
                INSERT INTO t_user
                    (username, password, salt, nickname)
                VALUES (?, ?, ?, ?);
                """,
                (username, password_hash, salt, username)
            )

            # 注册成功后跳转到登录页
            return redirect(url_for('auth.login'))

    return render_template('register.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
