import uuid
from functools import wraps

import redis
from flask import session, request, abort, redirect, url_for

from models.user import User
from utils import log


cache = redis.StrictRedis()


def current_user():
    if 'session_id' in request.cookies:
        session_id = request.cookies['session_id']
        key = 'session_id_{}'.format(session_id)
        if cache.get(key) is not None:
            user_id = int(cache.get(key))
            u: User = User.one(id=user_id)
            return u
        else:
            return None
    else:
        print('current_user None')
        return None


def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args['token']
        u = current_user()
        # csrf_token 改为存在 redis 的 cache 中
        if cache.exists(token) and int(cache.get(token)) == u.id:
            cache.delete(token)
            return f(*args, **kwargs)
        else:
            abort(401)

    return wrapper


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        print('current_user :', u)
        if u is not None:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index.index'))

    return wrapper


def new_csrf_token():
    u = current_user()
    token = str(uuid.uuid4())
    # csrf_token 改为存在 redis 的 cache 中
    cache.set(token, u.id, ex=3600)
    return token



