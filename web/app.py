#!/usr/bin/env python3

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

import time
import secret
from models.base_model import db
from models.reply import Reply
from models.topic import Topic
from models.user import User

from routes import current_user
from routes.index import main as index_routes
from routes.topic import main as topic_routes
from routes.reply import main as reply_routes
from routes.board import main as board_routes
from routes.message import main as mail_routes

from utils import formatted_time

import tests


class UserModelView(ModelView):
    column_searchable_list = ('username', 'password')


def configured_app():
    app = Flask(__name__)
    app.secret_key = secret.secret_key

    uri = 'mysql+pymysql://root:{}@localhost/web?charset=utf8mb4'.format(
        secret.database_password
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    admin = Admin(app, name='web admin', template_mode='bootstrap3')
    admin.add_view(UserModelView(User, db.session))

    register_routes(app)

    app.jinja_env.filters['time'] = formatted_time

    @app.context_processor
    def current():
        return dict(current_user=current_user)

    return app


def register_routes(app):
    # 注册蓝图
    app.register_blueprint(index_routes)
    app.register_blueprint(topic_routes, url_prefix='/topic')
    app.register_blueprint(reply_routes, url_prefix='/reply')
    app.register_blueprint(mail_routes, url_prefix='/message')
