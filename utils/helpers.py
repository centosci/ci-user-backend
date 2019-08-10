import flask
from models import *
import datetime

def get_current_ist_time():
    return datetime.datetime.utcnow()
    
def add_comment(request_id, user_id, comment):
    """
    Add comment on a project request.
    """
    
    new_comment = Comment(user_id=user_id, request_id=request_id, comment=comment)
    flask.g.session.add(new_comment)
    return {'result': 'success', 'message': 'Comment added successfully.'}

def create_project_for_request(req, user):
    """
    Add a new project for request
    """
    new_project = Project(project_name=req.project_name, description=req.project_desc)
    user_obj = flask.g.session.query(User).filter(User.username == user).one()
    flask.g.session.add(new_project)

    user_obj.projects.append(new_project)

    return {'result': 'success', 'message': 'Successfully reated new project.'}

def add_member_to_project(req, user):
    """
    Add user to existing project
    """
    project = flask.g.session.query(Project).filter(Project.project_name==req.project_name).one_or_none()
    if not project:
        return {'result': 'error', 'message': 'Project not found.'}
    
    user_obj = flask.g.session.query(User).filter(User.username == user).one()
    user_obj.projects.append(project)
    return {'result': 'success', 'message': 'Successfully created new project.'}
