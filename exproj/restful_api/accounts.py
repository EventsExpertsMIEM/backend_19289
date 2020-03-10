from flask import Blueprint
from flask_login import (login_required, login_user, logout_user,
                         login_fresh, current_user, fresh_login_required,
                         user_needs_refresh)

from . import *
from .. import accounts_logic
from ..db import USER_ACCESS

bp = Blueprint('accounts', __name__)


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
    login_user(user)  # todo: LOGIN???
    return make_ok('Logout from all other sessions')


@bp.route('/delete', methods=['POST'])
@login_required #@fresh_login_required
def self_delete():
    data = get_json()

    accounts_logic.self_delete(current_user.id, data['password'])
    logout_user()
    return make_ok('Successfully delete account')


@bp.route('/user/<int:u_id>/ban', methods=['GET'])
@login_required
def ban_user_by_id(u_id):
    accounts_logic.ban_user(u_id)
    return make_ok('Successfully banned this user')


@bp.route('/user/<int:u_id>/role', methods=['PUT'])
@login_required
def update_role(u_id):
    data = get_json()
    accounts_logic.update_role(u_id, data['role'])
    return make_ok('Successfully updated user\'s role')
