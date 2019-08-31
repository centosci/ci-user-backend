import uuid
import datetime
import flask
from sqlalchemy.dialects.postgresql import UUID
from application import db

def get_request_ref_id():
    latest_ref_id = flask.g.session.query(Request.reference_id).order_by(Request.created_at.desc()).first()
    if latest_ref_id:
        latest_ref_id = latest_ref_id[0]
    else:
        latest_ref_id = 1000
    return latest_ref_id + 1

class User(db.Model):

    __tablename__ = 'user'

    Roles = ['user', 'admin', 'superuser']

    id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, primary_key=True)
    username = db.Column(db.String())
    role = db.Column(db.Enum(*Roles, name='user_role'), default='user')
    email = db.Column(db.String())
    gpg_key = db.Column(db.String())
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)

    def __repr__(self):
        return f'<id {self.id}>'


class Request(db.Model):

    __tablename__ = 'request'

    RequestStatus = ['pending', 'approved', 'declined']

    id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, primary_key=True)
    user_id = db.Column(UUID(), db.ForeignKey(User.id), nullable=False)
    reference_id = db.Column(db.Integer, default=get_request_ref_id, unique=True)
    project_name = db.Column(db.String())
    project_desc = db.Column(db.String())
    status = db.Column(db.Enum(*RequestStatus, name='request_status'), default='pending')
    updated_by = db.Column(db.String())
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)

    def __repr__(self):
        return f'<id {self.id}>'


class Comment(db.Model):

    __tablename__ = 'comment'

    id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, primary_key=True)
    request_id = db.Column(UUID(), db.ForeignKey(Request.id), nullable=False)
    user_id = db.Column(UUID(), db.ForeignKey(User.id), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)

    def __repr__(self):
        return f'<id {self.id}>'


ProjectMember = db.Table(
    'project_member',
    db.Column('user_id', UUID(as_uuid=True), db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', UUID(as_uuid=True), db.ForeignKey('project.id'), primary_key=True)
    )


class Project(db.Model):

    __tablename__ = 'project'

    id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, primary_key=True)
    project_name = db.Column(db.String())
    description = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.datetime.now)
    members = db.relationship('User', secondary=ProjectMember, lazy=True, backref=db.backref('projects', lazy=True))

    def __repr__(self):
        return f'<id {self.id}>'
