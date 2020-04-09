import os
import sys
import logging
from contextlib import suppress

from flask import Flask, Request, abort
from flask_login import LoginManager
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from gevent import monkey

logger = logging.getLogger('exproj')
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)
logger.setLevel(logging.INFO)

from exproj import config
from exproj.logic.accounts import user_loader
from exproj.rest_api import accounts, users, posts, comments, tags
from exproj.db import Anonymous

def on_json_load_error(self, e):
    abort(415, 'Wrong json')
Request.on_json_loading_failed = on_json_load_error

app = Flask(__name__)
app.config.update(
    CSRF_ENABLED=config.CSRF_ENABLED,
    SECRET_KEY=config.SECRET_KEY,
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_HTTPONLY=False
)
CORS(app)

from . import errors

app.register_blueprint(accounts.bp)
app.register_blueprint(users.bp)
app.register_blueprint(posts.bp)
app.register_blueprint(comments.bp)
app.register_blueprint(tags.bp)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(user_loader)
login_manager.anonymous_user = Anonymous


def create_directories():
    with suppress(Exception):
        os.mkdir(config.FILE_UPLOADS.PARENT_DIRECTORY)
        os.mkdir(config.FILE_UPLOADS.TEMP_DIRECTORY)
        os.mkdir(config.FILE_UPLOADS.FILE_SETS.AVATAR.DIRECTORY)


def run_debug():
    logger.setLevel(logging.DEBUG)
    create_directories()
    logger.info('Started server in debug mode')
    app.run(host=config.HOST, port=config.PORT, debug=True)


def run():
    monkey.patch_all(ssl=False)
    http_server = WSGIServer((config.HOST, config.PORT), app)
    create_directories()
    logger.info('Started server')
    http_server.serve_forever()
