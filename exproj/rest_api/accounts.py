from flask import Blueprint, abort, jsonify
from flask_login import (login_required, login_user, logout_user,
                         current_user)

from . import make_ok, get_json
from exproj.logic import accounts as accounts_logic
from exproj.db import USER_ACCESS
from exproj.validation import schemas

bp = Blueprint('accounts', __name__)


@bp.route('/login_status')
def login_status():
    is_auth = current_user.is_authenticated

    status = dict(is_logged_in=is_auth)
    if is_auth:
        status['info'] = {
            'id': current_user.id,
            'name': current_user.name,
            'surname': current_user.surname,
            'email': current_user.email,
            'role': current_user.get_role()
        }

    return jsonify(status)


@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        abort(409, 'User is currently authenticated')

    data = get_json()

    user = accounts_logic.pre_login(data['email'], data['password'])
    login_user(user)
    return make_ok('User was logged in')


@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return make_ok('User was logged out')


@bp.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        abort(409, 'User is currently authenticated')

    data = get_json()
    schemas.registration.validate(data)

    accounts_logic.register_user(data)
    return make_ok('User was registered'), 201


@bp.route('/confirm', methods=['POST'])
def confirm():
    data = get_json()

    accounts_logic.confirm_user(data['link'])
    return make_ok('User was confirmed')


@bp.route('/change_password', methods=['POST'])
@login_required #@fresh_login_required
def change_password():
    data = get_json()

    user = accounts_logic.change_password(current_user.id,
                                          data['old_password'],
                                          data['new_password'])
    login_user(user)
    return make_ok('Password has beed changed')


@bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = get_json()

    accounts_logic.reset_password(data['email'])
    return make_ok('Successfully reset password - see new in your email')


@bp.route('/close_all_sessions', methods=['POST'])
@login_required #@fresh_login_required
def close_all_sessions():
    data = get_json()

    user = accounts_logic.close_all_sessions(current_user.id, data['password'])
    login_user(user)
    return make_ok('Logout from all other sessions')


@bp.route('/delete', methods=['POST'])
@login_required #@fresh_login_required
def self_delete():
    data = get_json()

    accounts_logic.self_delete(current_user.id, data['password'])
    logout_user()
    return make_ok('Successfully delete account')


@bp.route('/user/<int:u_id>/ban')
@login_required
def ban_user_by_id(u_id):
    accounts_logic.ban_user(u_id)
    return make_ok('Successfully banned this user')


@bp.route('/user/<int:u_id>/role/<role>')
@login_required
def update_role(u_id, role):
    if any([not current_user.has_access('moderator'),
            not current_user.has_access('admin') and role == 'moderator',
            not current_user.has_access('superadmin') and role == 'admin',
            role == 'superadmin']):
        abort(403)

    if role == 'superadmin' or role not in USER_ACCESS.keys():
        abort(422, 'Unknown role')

    accounts_logic.update_role(u_id, role)
    return make_ok('Successfully updated user\'s role')
