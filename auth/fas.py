from functools import wraps
import flask
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

        if request_wants_json():
            output = request.getMessage(trust_root,
                                        return_to=return_to).toPostArgs()
            output['server_url'] = request.endpoint.server_url
            return flask.jsonify(output)
        elif request.shouldSendRedirect():
            redirect_url = request.redirectURL(trust_root, return_to, False)
            return flask.redirect(redirect_url)
        elif not return_to_same_app:
            redirect_url = request.redirectURL(trust_root, return_to, False)
            return redirect_url
        else:
            return request.htmlMarkup(
                trust_root, return_to,
                form_tag_attrs={'id': 'openid_message'}, immediate=False)

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