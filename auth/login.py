import os
import flask
from flask import jsonify, Blueprint
from application import app
from models import User
from auth.fas import newFAS

auth = Blueprint('auth', __name__)
fas = newFAS(app)


@auth.route('/login', methods=['GET', 'POST'])
def auth_login():
    """
    Method to log into the application using FAS OpenID.
    """
    if flask.session.get('FLASK_FAS_OPENID_USER'):
        return f'{os.environ["CLIENT_URL"]}/projects'
    return fas.login(return_url=f'{os.environ["CLIENT_URL"]}/projects')


@auth.route('/logout')
def auth_logout():
    """
    Method to log out currently logged in user from the application.

    """
    if not flask.session.get('FLASK_FAS_OPENID_USER'):
        return jsonify({'result': 'error', 'message': 'User is already logged out.'}), 200

    fas.logout()
    return jsonify({'result': 'success', 'message': 'You have successfully logged out'}), 200


@fas.postlogin
def set_user(return_url):
    """
    Set up user in app after FAS login.
    """

    if not flask.session.get('FLASK_FAS_OPENID_USER').get('username'):
        fas.logout()
        return jsonify({'redirect_url': return_url}), 200

    user = flask.g.session.query(User).filter(User.username == flask.session['FLASK_FAS_OPENID_USER'].get('username'),
                                              User.email == flask.session['FLASK_FAS_OPENID_USER'].get('email')).one_or_none()
    if not user:
        new_user = User(
            username=flask.session['FLASK_FAS_OPENID_USER']['username'],
            email=flask.session['FLASK_FAS_OPENID_USER']['email'],
            gpg_key=flask.session['FLASK_FAS_OPENID_USER'].get('gpg_keyid'),
        )
        flask.g.session.add(new_user)
        flask.g.session.commit()

    return jsonify({'redirect_url': return_url}), 200
