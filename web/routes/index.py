import os
import uuid

from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    Blueprint,
    abort,
    send_from_directory,
    current_app,
    make_response
    )
from werkzeug.datastructures import FileStorage

import secret
from models.message import Messages
from models.reply import Reply
from models.topic import Topic
from models.user import User
from routes import current_user, cache
from routes import current_user, csrf_required, login_required

import json
import time

from utils import log

main = Blueprint('index', __name__)


@main.route("/")
def index():
    time.sleep(0.5)
    return render_template('login.html')


@main.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form.to_dict()
        u = User.register(form)
        log('注册成功!')
        return redirect(url_for('.index'))

    return render_template('register.html')


@main.route("/login", methods=['GET', 'POST'])
def login():
    form = request.form
    u = User.validate_login(form)
    if u is None:
        log('账号或密码错误，登录失败!')
        return redirect(url_for('.index'))
    else:
        # flask session 改为 redis 存储的session
        session_id = str(uuid.uuid4())
        key = 'session_id_{}'.format(session_id)
        cache.set(key, u.id)

        redirect_to_index = redirect(url_for('topic.index'))
        response = current_app.make_response(redirect_to_index)
        response.set_cookie('session_id', value=session_id, max_age=3600)

        return response


@main.route("/logout", methods=['GET'])
@login_required
def logout():
    redirect_to_index = redirect(url_for('.index'))
    response = current_app.make_response(redirect_to_index)
    response.delete_cookie('session_id')

    return response


def created_topic(user_id):
    ts = Topic.all(user_id=user_id)
    return ts


def replied_topic(user_id):
    k = 'replied_topic_{}'.format(user_id)
    if cache.exists(k):
        v = cache.get(k)
        ts = json.loads(v)
        return ts
    else:
        rs = Reply.all(user_id=user_id)
        ts = []
        for r in rs:
            t = Topic.one(id=r.topic_id)
            ts.append(t)

        v = json.dumps([t.json() for t in ts])
        cache.set(k, v)

        return ts


@main.route('/profile')
@login_required
def profile():
    u = current_user()
    if u is None:
        return redirect(url_for('.index'))
    else:
        created = created_topic(u.id)
        replied = replied_topic(u.id)
        return render_template(
            'profile.html',
            user=u,
            created=created,
            replied=replied
        )


@main.route('/user/<int:id>')
@login_required
def user_detail(id):
    u = User.one(id=id)
    if u is None:
        abort(404)
    else:
        return render_template('profile.html', user=u)


@main.route('/image/add', methods=['POST'])
@login_required
def avatar_add():
    file: FileStorage = request.files['avatar']
    suffix = file.filename.split('.')[-1]
    if suffix not in ['gif', 'jpg', 'jpeg', 'png']:
        abort(400)
        log('不接受的后缀, {}'.format(suffix))
    else:
        filename = '{}.{}'.format(str(uuid.uuid4()), suffix)
        path = os.path.join('images', filename)
        file.save(path)

        u = current_user()
        User.update(u.id, image='/images/{}'.format(filename))

        return redirect(url_for('.profile'))


@main.route('/images/<filename>')
@login_required
def image(filename):
    return send_from_directory('images', filename)


@main.route('/setting', methods=['GET', 'POST'])
@login_required
def setting():
    u = current_user()
    if request.method == 'POST':
        username = request.form['username']
        signature = request.form['signature']
        u.update(id=u.id, username=username, signature=signature)
        log('修改用户名和个性签名成功')

    return render_template('setting.html', user=u)


@main.route('/setting/update_password', methods=['GET', 'POST'])
def setting_update_password():
    u = current_user()
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        if u.salted_password(old_password) == u.password:
            u.password = u.salted_password(new_password)
            u.update(id=u.id, password=u.password)
            log('修改密码成功')

    return render_template('setting.html', user=u)


@main.route('/reset', methods=['GET', 'POST'])
def reset_password():
    return render_template('reset.html')


@main.route('/reset/send', methods=['GET', 'POST'])
def reset():
    """
    找回密码
    """
    username = request.form['username']
    u = User.one(username=username)

    token = str(uuid.uuid4())
    cache.set(token, u.id, ex=3600)

    content = '{}/reset/view?token={}'.format(secret.dns, token)
    Messages.send(
        title='找回密码',
        content=content,
        sender_id=u.id,
        receiver_id=u.id
    )

    return redirect(url_for('.index'))


@main.route('/reset/view', methods=['GET', 'POST'])
def reset_view():
    token = request.args['token']
    if token is not None:
        return render_template('reset_view.html', token=token)
    else:
        return redirect(url_for('.index'))


@main.route('/reset/update/<token>', methods=['GET', 'POST'])
def reset_update(token):
    if token is not None:
        user_id = cache.get(token)
        log('user_id:', user_id)
        u = User.one(id=int(user_id))
        new_password = request.form['password']

        u.update(id=user_id, password=u.salted_password(new_password))
        log('重置密码成功')

    return redirect(url_for('.index'))

