import pytest
from cryptography.fernet import Fernet

from backend.app import create_app
from backend.crypto import reset_cipher


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('ENVAULT_SECRET_KEY', Fernet.generate_key().decode('utf-8'))
    reset_cipher()
    db_file = tmp_path / 'envault_test.db'
    app = create_app(f'sqlite:///{db_file}')
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client
    reset_cipher()


def test_health_and_project_crud_validation(client):
    assert client.get('/health').get_json() == {'status': 'ok'}

    assert client.post('/api/projects', json={'name': '   '}).status_code == 400

    res = client.post('/api/projects', json={'name': 'payments', 'description': 'prod secrets'})
    assert res.status_code == 201
    pid = res.get_json()['id']

    dup = client.post('/api/projects', json={'name': 'payments'})
    assert dup.status_code == 409

    projects = client.get('/api/projects').get_json()
    assert len(projects) == 1
    assert projects[0]['name'] == 'payments'

    assert client.delete(f'/api/projects/{pid}').status_code == 200
    assert client.delete(f'/api/projects/{pid}').status_code == 404


def test_encrypted_variables_history_and_safe_env_export(client):
    pid = client.post('/api/projects', json={'name': 'core'}).get_json()['id']

    assert client.post('/api/projects/9999/variables', json={'key': 'API_KEY', 'value': 'abc'}).status_code == 404
    assert client.post(f'/api/projects/{pid}/variables', json={'key': 'BAD KEY=1', 'value': 'abc'}).status_code == 400

    var_res = client.post(
        f'/api/projects/{pid}/variables',
        json={'key': 'WEBHOOK_SECRET', 'value': 'line1\nline2 #comment'},
    )
    assert var_res.status_code == 201
    vid = var_res.get_json()['id']

    vars_list = client.get(f'/api/projects/{pid}/variables').get_json()
    assert len(vars_list) == 1
    assert vars_list[0]['value'] == 'line1\nline2 #comment'

    assert client.put(f'/api/variables/{vid}', json={'value': 'rotated_val'}).status_code == 200

    history = client.get(f'/api/variables/{vid}/history').get_json()
    assert len(history) == 2
    assert history[0]['new_value'] == 'rotated_val'
    assert history[0]['old_value'] == 'line1\nline2 #comment'

    client.post(f'/api/projects/{pid}/variables', json={'key': 'APP_ENV', 'value': 'production'})
    export_res = client.get(f'/api/projects/{pid}/export')
    assert export_res.status_code == 200
    text = export_res.get_data(as_text=True)
    assert 'WEBHOOK_SECRET=rotated_val' in text
    assert 'APP_ENV=production' in text
