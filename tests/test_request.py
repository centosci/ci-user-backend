from models import *
import json

def test_create_request_without_login(test_client, dbsession):
    resp = test_client.post('/new-request', data=json.dumps({"project_name": 'test_project1'}))
    data = json.loads(resp.data)
    assert data['result'] == 'error'
    assert data['message'] == 'Please log in to continue.'

def test_get_projects(test_client, dbsession):
    p = Project(project_name='test_project1')
    dbsession.add(p)
    dbsession.commit()
    resp = test_client.get('/projects')
    data = json.loads(resp.data)
    assert data['projects'][0]['project_name'] == 'test_project1'