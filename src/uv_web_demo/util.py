import base64
import hashlib
import hmac
import json
import os
from functools import wraps

from flask import jsonify, session, redirect, url_for, request


class JsonResult:
    def __init__(self, success: bool, message: str, data: object):
        self.success = success
        self.message = message
        self.data = data

    def res(self):
        return jsonify({
            'success': self.success,
            'message': self.message,
            'data': self.data
        })

    @staticmethod
    def successful(message: str = 'ok', data: object = None):
        return JsonResult(True, message, data).res()

    @staticmethod
    def failed(message: str = 'fail', data: object = None):
        return JsonResult(False, message, data).res()


class PasswordUtil:

    ITERATIONS = 65536
    KEY_LENGTH = 32  # 256 位 / 8
    ALGORITHM = 'sha256'

    @staticmethod
    def generate_salt(length: int = 16) -> str:
        """生成随机 Salt（Base64 编码）"""
        salt_bytes = os.urandom(length)
        return base64.b64encode(salt_bytes).decode('utf-8')

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """生成密码哈希（PBKDF2 + Salt + Base64 编码）"""
        salt_bytes = base64.b64decode(salt)
        dk = hashlib.pbkdf2_hmac(
            PasswordUtil.ALGORITHM,
            password.encode('utf-8'),
            salt_bytes,
            PasswordUtil.ITERATIONS,
            dklen=PasswordUtil.KEY_LENGTH
        )
        return base64.b64encode(dk).decode('utf-8')

    @staticmethod
    def verify_password(input_password: str, stored_hash: str, stored_salt: str) -> bool:
        """验证密码"""
        new_hash = PasswordUtil.hash_password(input_password, stored_salt)
        return hmac.compare_digest(new_hash, stored_hash)


class ChapterUtil:
    @staticmethod
    def generate_chapters(book_id: int, chapters_text: str) -> list:
        try:
            chapters_data = json.loads(chapters_text)
        except json.JSONDecodeError:
            chapters_data = []

        chapters = []
        for order_index, c in enumerate(chapters_data):
            try:
                chapter_num = c.get('chapter')
                if chapter_num is not None:
                    chapter_num = int(chapter_num)
            except ValueError:
                continue
            content = (c.get('content') or '').strip()
            chapter_title = (c.get('chapter_title') or '').strip()
            content_hash = cal_content_hash(chapter_num, chapter_title, order_index, content)
            chapter_id = c.get('chapter_id')
            if chapter_id:
                chapter_id = int(chapter_id)
            if (chapter_num or chapter_title) and content:
                chapters.append({
                    'book_id': book_id,
                    'chapter_id': chapter_id,
                    'chapter': chapter_num,
                    'chapter_title': chapter_title,
                    'content': content,
                    'order_index': order_index,
                    'content_hash': content_hash,
                })
        return chapters

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # 记录原始请求路径，登录后跳转回来
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


def cal_content_hash(chapter_num, chapter_title, order_index, content) -> str:
    hash_text = f'{chapter_num}{chapter_title}{order_index}{content}'
    return hashlib.md5(hash_text.encode('utf-8')).hexdigest()