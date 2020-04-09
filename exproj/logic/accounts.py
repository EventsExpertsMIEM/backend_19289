import logging
import bcrypt
import nanoid
import uuid

from flask import abort
from flask_login import current_user

from exproj import config, util
from exproj.db import get_session, USER_ACCESS, User


def user_loader(cookie_id):
    with get_session() as s:
        return s.query(User).filter(
            User.cookie_id == cookie_id,
            User.status == 'active'
        ).one_or_none()


def pre_login(email, password):
    with get_session() as s:
        user = s.query(User).filter(
            User.email == email
        ).one_or_none()

        if not user or user.status == 'deleted':
            abort(404, 'User not found')
        if user.status == 'banned':
            abort(409, 'Trying to login banned user!')

        pw = str(password).encode('utf-8')
        upw = str(user.password).encode('utf-8')
        if not bcrypt.checkpw(pw, upw):
            abort(422, 'Invalid password')
        return user


def register_user(data):
    with get_session() as s:
        user = s.query(User).filter(
            User.email == data['email']
        ).one_or_none()

        # checking unique link
        while True:
            confirmation_link = nanoid.generate(size=50)
            exists = s.query(User).filter(
                User.confirmation_link == confirmation_link
            ).one_or_none()
            if not exists:
                break

        pw = bcrypt.hashpw(str(data['password']).encode('utf-8'),
                           bcrypt.gensalt()).decode('utf-8')

        if user:
            if user.status == 'deleted':
                user.password = pw
                user.name = data['name']
                user.surname = data['surname']
                user.status = config.DEFAULT_USER_STATUS
                user.confirmation_link = confirmation_link
            elif user.status == 'banned':
                abort(409, 'User with this email was banned')
            else:
                abort(409, 'Trying to register existing user')
        else:
            user = User(email=data['email'],
                        name=data['name'],
                        surname=data['surname'],
                        password=pw,
                        confirmation_link=confirmation_link)
            s.add(user)
        if config.DEFAULT_USER_STATUS == 'unconfirmed':
            util.send_email(data['email'], confirmation_link)
        logging.info('Registering new user [{}]'.format(data['email']))


def confirm_user(confirmation_link):
    with get_session() as s:
        user = s.query(User).filter(
            User.confirmation_link == confirmation_link
        ).one_or_none()
        if user:
            if user.status == 'unconfirmed':
                user.status = 'active'
                logging.info('User [{}] is confirmed'.format(user.email))
            else:
                abort(409, 'User is currently confirmed by '
                           'this link or can\'t be confirmed')

        abort(404, 'No user with this confirmation link')


def change_password(u_id, old_password, new_password):
    with get_session() as s:
        u = User.get_or_404(s, u_id)
        opw = str(old_password).encode('utf-8')
        npw = str(new_password).encode('utf-8')
        pw = str(u.password).encode('utf-8')

        if not bcrypt.checkpw(opw, pw):
            abort(422, 'Invalid password')
        if bcrypt.checkpw(npw, pw):
            abort(422, 'Old and new passwords are equal')
        npw = bcrypt.hashpw(npw, bcrypt.gensalt())
        u.password = npw.decode('utf-8')
        u.cookie_id = uuid.uuid4()
        return u


def reset_password(email):
    with get_session() as s:
        user = s.query(User).filter(
            User.email == email,
            User.status == 'active'
        ).one_or_none()

        if not user:
            abort(404, 'Invalid user')

        new_password = util.random_string_digits(20)
        npw = bcrypt.hashpw(str(new_password).encode('utf-8'), bcrypt.gensalt())
        user.password = npw.decode('utf-8')
        user.cookie_id = uuid.uuid4()
        util.send_reset_email(email, new_password)


def close_all_sessions(u_id, password):
    with get_session() as s:
        u = User.get_or_404(s, u_id)
        opw = str(password).encode('utf-8')
        pw = str(u.password).encode('utf-8')
        if not bcrypt.checkpw(opw, pw):
            abort(422, 'Invalid password')
        u.cookie_id = uuid.uuid4()
        return u


def self_delete(u_id, password):
    with get_session() as s:
        u = User.get_or_404(s, u_id)
        opw = str(password).encode('utf-8')
        pw = str(u.password).encode('utf-8')
        if not bcrypt.checkpw(opw, pw):
            abort(422, 'Invalid password')
        u.status = 'deleted'


def ban_user(u_id):
    with get_session() as s:
        u = User.get_or_404(s, u_id)

        if (u.has_access('moderator')
                or not current_user.has_access('moderator')):
            abort(403)

        if u.status == 'banned':
            abort(409, 'User has already banned')

        u.status = 'banned'


def update_role(u_id, role):
    with get_session() as s:
        u = User.get_or_404(s, u_id)

        if u.access == USER_ACCESS[role]:
            abort(409, 'User already has that role')

        u.access = USER_ACCESS[role]
