from functools import wraps
import flask
import os
import time
from flask_fas_openid import FAS, request_wants_json, FASJSONEncoder
from openid.extensions import pape, sreg, ax
from openid.consumer import consumer
from openid_teams import teams
from openid_cla import cla
import six

class newFAS(FAS):

    def init_app(self, app):
        """ Constructor for the Flask application. """
        self.app = app
        app.config.setdefault('FAS_OPENID_ENDPOINT',
                              'https://id.fedoraproject.org/openid/')
        app.config.setdefault('FAS_OPENID_CHECK_CERT', True)

        if not self.app.config['FAS_OPENID_CHECK_CERT']:
            setDefaultFetcher(Urllib2Fetcher())

        # json_encoder is only available from flask 0.10
        version = flask.__version__.split('.')
        assume_recent = False
        try:
            major = int(version[0])
            minor = int(version[1])
        except ValueError:
            # We'll assume we're using a recent enough flask as the packages
            # of old versions used sane version numbers.
            assume_recent = True

        if assume_recent or (major > 0 or minor >= 10):
            self.app.json_encoder = FASJSONEncoder

        @app.route('/_flask_fas_openid_handler/', methods=['GET', 'POST'])
        def flask_fas_openid_handler():
            """ Endpoint for OpenID results. """
            return self._handle_openid_request()

        app.before_request(self._check_session)

    def login(self, username=None, password=None, return_url=None,
              cancel_url=None, groups=['_FAS_ALL_GROUPS_']):
        """
        Copied from the FAS Flask OpenID Auth Plugin with modifications to be
        compatible with a separate frontend application.
        """

        if return_url is None:
            if 'next' in flask.request.args.values():
                return_url = flask.request.args.values['next']
            else:
                return_url = flask.request.url_root

        return_to_same_app =  self._check_safe_root(return_url)
            
        session = {}
        oidconsumer = consumer.Consumer(session, None)
        try:
            request = oidconsumer.begin(self.app.config['FAS_OPENID_ENDPOINT'])
        except consumer.DiscoveryFailure as exc:
            # VERY strange, as this means it could not discover an OpenID
            # endpoint at FAS_OPENID_ENDPOINT
            log.warn(exc)
            return 'discoveryfailure'
        if request is None:
            # Also very strange, as this means the discovered OpenID
            # endpoint is no OpenID endpoint
            return 'no-request'

        if isinstance(groups, six.string_types):
            groups = [groups]

        request.addExtension(sreg.SRegRequest(
            required=['nickname', 'fullname', 'email', 'timezone']))
        request.addExtension(pape.Request([]))
        request.addExtension(teams.TeamsRequest(requested=groups))
        request.addExtension(cla.CLARequest(
            requested=[cla.CLA_URI_FEDORA_DONE]))

        ax_req = ax.FetchRequest()
        ax_req.add(ax.AttrInfo(
            type_uri='http://fedoauth.org/openid/schema/GPG/keyid'))
        ax_req.add(ax.AttrInfo(
            type_uri='http://fedoauth.org/openid/schema/SSH/key',
            count='unlimited'))
        request.addExtension(ax_req)

        trust_root = self.normalize_url(flask.request.url_root)
        return_to = trust_root + '_flask_fas_openid_handler/'
        flask.session['FLASK_FAS_OPENID_RETURN_URL'] = return_url
        flask.session['FLASK_FAS_OPENID_CANCEL_URL'] = cancel_url
        flask.session.modified = True

        if request_wants_json():
            output = request.getMessage(trust_root,
                                        return_to=return_to).toPostArgs()
            output['server_url'] = request.endpoint.server_url
            return flask.jsonify(output)
        elif request.shouldSendRedirect():
            redirect_url = request.redirectURL(trust_root, return_to, False)
            return flask.redirect(redirect_url)
        elif not return_to_same_app:
            return_to = os.environ['CLIENT_URL'] + '/_flask_fas_openid_handler/'
            redirect_url = request.redirectURL(os.environ['CLIENT_URL'], return_to, False)
            return redirect_url
        else:
            return request.htmlMarkup(
                trust_root, return_to,
                form_tag_attrs={'id': 'openid_message'}, immediate=False)

    def _handle_openid_request(self):
        return_url = flask.session.get('FLASK_FAS_OPENID_RETURN_URL', None)
        cancel_url = flask.session.get('FLASK_FAS_OPENID_CANCEL_URL', None)
        base_url = self.normalize_url(flask.request.base_url)
        oidconsumer = consumer.Consumer(flask.session, None)
        info = oidconsumer.complete(flask.request.values, os.environ['CLIENT_URL'] + '/_flask_fas_openid_handler/')
        display_identifier = info.getDisplayIdentifier()
        
        if info.status == consumer.FAILURE and display_identifier:
            return 'FAILURE. display_identifier: %s' % display_identifier
        elif info.status == consumer.CANCEL:
            if cancel_url:
                return flask.redirect(cancel_url)
            return 'OpenID request was cancelled'
        elif info.status == consumer.SUCCESS:
            if info.endpoint.server_url != \
                    self.app.config['FAS_OPENID_ENDPOINT']:
                log.warn('Claim received from invalid issuer: %s',
                         info.endpoint.server_url)
                return 'Invalid provider issued claim!'

            sreg_resp = sreg.SRegResponse.fromSuccessResponse(info)
            teams_resp = teams.TeamsResponse.fromSuccessResponse(info)
            cla_resp = cla.CLAResponse.fromSuccessResponse(info)
            ax_resp = ax.FetchResponse.fromSuccessResponse(info)
            user = {'fullname': '', 'username': '', 'email': '',
                    'timezone': '', 'cla_done': False, 'groups': []}
            if not sreg_resp:
                # If we have no basic info, be gone with them!
                return flask.redirect(cancel_url)
            user['username'] = sreg_resp.get('nickname')
            user['fullname'] = sreg_resp.get('fullname')
            user['email'] = sreg_resp.get('email')
            user['timezone'] = sreg_resp.get('timezone')
            user['login_time'] = time.time()
            if cla_resp:
                user['cla_done'] = cla.CLA_URI_FEDORA_DONE in cla_resp.clas
            if teams_resp:
                # The groups do not contain the cla_ groups
                user['groups'] = frozenset(teams_resp.teams)
            if ax_resp:
                ssh_keys = ax_resp.get(
                    'http://fedoauth.org/openid/schema/SSH/key')
                if isinstance(ssh_keys, (list, tuple)):
                    ssh_keys = '\n'.join(
                        ssh_key
                        for ssh_key in ssh_keys
                        if ssh_key.strip()
                    )
                    if ssh_keys:
                        user['ssh_key'] = ssh_keys
                user['gpg_keyid'] = ax_resp.get(
                    'http://fedoauth.org/openid/schema/GPG/keyid')
            flask.session['FLASK_FAS_OPENID_USER'] = user
            flask.session.modified = True
            if self.postlogin_func is not None:
                self._check_session()
                return self.postlogin_func(return_url)
            else:
                return flask.redirect(return_url)
        else:
            return 'Strange state: %s' % info.status

def fas_login_required(function):
    """ Flask decorator to ensure that the user is logged in against FAS.
    To use this decorator you need to have a function named 'auth_login'.
    Without that function the redirect if the user is not logged in will not
    work.
    """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not flask.session.get('FLASK_FAS_OPENID_USER'):
            return flask.jsonify({'result': 'error', 'message': 'Please log in to continue.'}), 200
        return function(*args, **kwargs)
    return decorated_function