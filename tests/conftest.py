import flask
import pytest
from collections import namedtuple
from application import create_app
from application import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from utils.init_app_helpers import create_session

@pytest.fixture(scope='session')
def app(request):
    """
    Session-wide application instance for testing.
    """
    a = create_app()
    a.config.from_object("config.TestingConfig")
    a.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test_user:test123@localhost:5432/test_db'
    # Establish an application context before running the tests.
    ctx = a.test_request_context()
    ctx.push()
    yield a
    # app teardown here
    # ctx.pop()


@pytest.fixture(scope='session')
def test_client(app):
    # create the test client instance
    _test_client = app.test_client()
    yield _test_client


@pytest.fixture(scope='session')
def dbsession(app):
    """
    Session-wide test database
    """
    db.create_all()
    s = create_session(flask.current_app.config["SQLALCHEMY_DATABASE_URI"])
    yield s
    
    s.close()
    db.drop_all()

# @pytest.fixture(scope='session', autouse=True)
# def generate_database_fixture(db):
#     file = generate_database(db)
#     db.session.commit()
#     yield file
