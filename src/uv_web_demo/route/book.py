import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app

from ..app_config import AppConfig
from ..db import DB
from ..util import login_required, ChapterUtil, cal_content_hash

book_bp = Blueprint('book', __name__)
app_logger = logging.getLogger(AppConfig.PROJECT_NAME + "." + __name__)


@book_bp.get('/book')
@login_required
def book():
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    total = DB.query("SELECT COUNT(*) as cnt FROM t_book")[0]['cnt']

    books = DB.query(
        """
        SELECT *
        FROM t_book
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset)
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'book.html', books=books, page=page, total_pages=total_pages
    )


@book_bp.get('/book_table/<int:book_id>')
def book_table(book_id):
    book_entity = DB.query("SELECT * FROM t_book WHERE id = ?", [book_id])
    book_chapters = DB.query(
        "SELECT id, chapter, chapter_title FROM t_book_chapter where book_id = ? ORDER BY order_index", [book_id])
    app_logger.debug(f'book_entity: {book_entity}')
    app_logger.debug(f'book_chapter: {book_chapters}')
    return render_template('book_table.html', book=book_entity[0], book_chapters=book_chapters)


@book_bp.get('/book_chapter/<int:chapter_id>/')
def book_chapter(chapter_id):
    chapter = DB.query(
        """
        SELECT a.*,
               b.title as book_title
        FROM t_book_chapter as a
                 LEFT JOIN t_book as b ON a.book_id = b.id
        WHERE a.id = ?
        """, [chapter_id])[0]
    app_logger.debug(f'chapter: {chapter}')

    book_chapters = DB.query(
        "SELECT id, chapter, chapter_title FROM t_book_chapter where book_id = ? ORDER BY order_index", (chapter.get('book_id'),))

    return render_template('read.html', chapter=chapter, book_chapters=book_chapters)


@book_bp.route('/book/add', methods=['GET', 'POST'])
@login_required
def book_add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        publish_date = request.form['publish_date']

        # 处理封面上传
        cover_file = request.files['cover']
        cover_path = None
        if cover_file and cover_file.filename:
            ext = Path(cover_file.filename).suffix
            cover_name = f"{uuid.uuid4().hex}{ext}"
            cover_path = Path(current_app.config['UPLOAD_FOLDER']) / 'covers' / cover_name
            cover_path.parent.mkdir(parents=True, exist_ok=True)
            cover_file.save(cover_path)
            cover_path = f"assets/covers/{cover_name}"

        book_id = DB.execute(
            """
            INSERT INTO t_book (title, description, publish_date, cover_image_path, create_datetime,
                                update_datetime)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title, description, publish_date, cover_path,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )

        # 处理章节内容
        chapters_text = request.form.get('chapters', '').strip()
        save_chapters(book_id, chapters_text)
        flash("Book added successfully!", "success")
        return redirect(url_for('book.book'))

    return render_template('book_edit.html', book=None, chapters=None)


@book_bp.route('/book/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book_edit(book_id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        publish_date = request.form['publish_date']

        cover_file = request.files['cover']
        cover_path = request.form.get('existing_cover')

        if cover_file and cover_file.filename:
            ext = Path(cover_file.filename).suffix
            cover_name = f"{uuid.uuid4().hex}{ext}"
            cover_path = Path(current_app.config['UPLOAD_FOLDER']) / 'covers' / cover_name
            cover_path.parent.mkdir(parents=True, exist_ok=True)
            cover_file.save(cover_path)
            cover_path = f"assets/covers/{cover_name}"

        DB.execute(
            """
            UPDATE t_book
            SET title=?,
                description=?,
                publish_date=?,
                cover_image_path=?,
                update_datetime=?
            WHERE id = ?
            """,
            (
                title, description, publish_date, cover_path,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), book_id
            )
        )

        # 先删掉旧章节
        # DB.execute("DELETE FROM t_book_chapter WHERE book_id=?", (book_id,))

        # 处理章节内容
        chapters_text = request.form.get('chapters', '').strip()
        save_chapters(book_id, chapters_text)

        flash("Book updated successfully!", "success")
        return redirect(url_for('book.book'))

    book_data = DB.query("SELECT * FROM t_book WHERE id=?", (book_id,))[0]
    chapters = DB.query(
        "SELECT a.id as chapter_id, a.* FROM t_book_chapter AS a WHERE book_id=? ORDER BY a.order_index ASC",
        (book_id,)
    )

    return render_template('book_edit.html', book=book_data, chapters=chapters)


@book_bp.post('/book/delete/<int:book_id>')
@login_required
def book_delete(book_id):
    book_cover_path = DB.query("SELECT cover_image_path FROM t_book WHERE id=?", (book_id,))[0]['cover_image_path']
    if book_cover_path:
        cover_abs_path = Path(current_app.static_folder) / book_cover_path
        if cover_abs_path.exists():
            try:
                cover_abs_path.unlink()
            except Exception as e:
                app_logger.exception(f"Failed to delete cover file {cover_abs_path}: {e}")

    DB.execute("DELETE FROM t_book WHERE id=?", (book_id,))
    DB.execute("DELETE FROM t_book_chapter WHERE book_id=?", (book_id,))
    flash("Book deleted successfully!", "success")
    return redirect(url_for('book.book'))


def save_chapters(book_id, chapters_text):
    saved_chapter_ids = []
    if chapters_text:
        chapters = ChapterUtil.generate_chapters(book_id, chapters_text)

        chapter_ids = set([c.get('chapter_id') for c in chapters if c.get('chapter_id') is not None])
        db_chapters = DB.query("SELECT id, book_id, content_hash FROM t_book_chapter WHERE book_id = ?", (book_id,))
        db_chapter_ids = set([c.get('id') for c in db_chapters])
        db_chapters_map = {c.get('id'): c.get('content_hash') for c in db_chapters}

        deleted_chapter_ids = db_chapter_ids - chapter_ids

        if deleted_chapter_ids:
            placeholders = ','.join(['?'] * len(deleted_chapter_ids))
            sql = f"DELETE FROM t_book_chapter WHERE id IN ({placeholders})"
            DB.execute(sql, tuple(deleted_chapter_ids))
            app_logger.debug(f"Deleted chapters: {deleted_chapter_ids}")

        # 批量插入章节
        for chapter in chapters:
            # 数据库已存在的章节
            if chapter.get('chapter_id'):
                # 根据 hash 判断是否需要更新
                content_hash = chapter.get('content_hash')
                if content_hash != db_chapters_map[chapter.get('chapter_id')]:
                    DB.execute(
                        "UPDATE t_book_chapter SET content_hash=?, chapter=?, chapter_title=?, content=?, order_index=? WHERE id=?",
                        (
                            chapter.get('content_hash'),
                            chapter.get('chapter'), chapter.get('chapter_title'),
                            chapter.get('content'), chapter.get('order_index'), chapter.get('chapter_id')
                        )
                    )
                    app_logger.info(f'Update chapter: {chapter.get("chapter_id")}')
                saved_chapter_ids.append(chapter.get('chapter_id'))
            else:
                # 新的章节
                cur_chapter_id = DB.execute(
                    """
                    INSERT INTO t_book_chapter (book_id, chapter, chapter_title, content, order_index, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chapter['book_id'], chapter['chapter'], chapter['chapter_title'],
                        chapter['content'], chapter['order_index'], chapter['content_hash']
                    )
                )
                saved_chapter_ids.append(cur_chapter_id)
                app_logger.info(f'Add new chapter: {cur_chapter_id}')

        if len(chapters) > 1:
            for i, chapter_id in enumerate(saved_chapter_ids):
                if i == 0:
                    DB.execute(
                        """
                        UPDATE t_book_chapter
                        SET next_id = ?
                        where id = ?
                        """,
                        (saved_chapter_ids[i + 1], chapter_id)
                    )
                elif i == len(saved_chapter_ids) - 1:
                    DB.execute(
                        """
                        UPDATE t_book_chapter
                        SET prev_id = ?
                        where id = ?
                        """,
                        (saved_chapter_ids[i - 1], chapter_id)
                    )
                else:
                    DB.execute(
                        """
                        UPDATE t_book_chapter
                        SET prev_id = ?,
                            next_id = ?
                        where id = ?
                        """,
                        (saved_chapter_ids[i - 1], saved_chapter_ids[i + 1], chapter_id)
                    )
