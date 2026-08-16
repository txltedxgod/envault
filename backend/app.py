from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Project, Variable, VariableHistory
from crypto import encrypt, decrypt

app = Flask(__name__)
CORS(app)

engine = create_engine('sqlite:///envault.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@app.route('/api/projects', methods=['GET'])
def list_projects():
    session = Session()
    projects = session.query(Project).order_by(Project.created_at.desc()).all()
    result = []
    for p in projects:
        result.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'var_count': len(p.variables),
            'created_at': p.created_at.isoformat()
        })
    session.close()
    return jsonify(result)


@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    session = Session()
    project = Project(name=data['name'], description=data.get('description', ''))
    session.add(project)
    session.commit()
    pid = project.id
    session.close()
    return jsonify({'id': pid, 'name': data['name']}), 201


@app.route('/api/projects/<int:pid>', methods=['DELETE'])
def delete_project(pid):
    session = Session()
    project = session.query(Project).get(pid)
    if not project:
        session.close()
        return jsonify({'error': 'not found'}), 404
    session.delete(project)
    session.commit()
    session.close()
    return jsonify({'ok': True})


@app.route('/api/projects/<int:pid>/variables', methods=['GET'])
def list_variables(pid):
    session = Session()
    variables = session.query(Variable).filter_by(project_id=pid).all()
    result = []
    for v in variables:
        result.append({
            'id': v.id,
            'key': v.key,
            'value': decrypt(v.value_encrypted),
            'updated_at': v.updated_at.isoformat()
        })
    session.close()
    return jsonify(result)


@app.route('/api/projects/<int:pid>/variables', methods=['POST'])
def add_variable(pid):
    data = request.json
    session = Session()
    var = Variable(
        project_id=pid,
        key=data['key'],
        value_encrypted=encrypt(data['value'])
    )
    session.add(var)
    session.commit()

    # record history
    history = VariableHistory(
        variable_id=var.id,
        new_value_encrypted=var.value_encrypted
    )
    session.add(history)
    session.commit()
    session.close()
    return jsonify({'id': var.id, 'key': data['key']}), 201


@app.route('/api/variables/<int:vid>', methods=['PUT'])
def update_variable(vid):
    data = request.json
    session = Session()
    var = session.query(Variable).get(vid)
    if not var:
        session.close()
        return jsonify({'error': 'not found'}), 404

    old_enc = var.value_encrypted
    var.key = data.get('key', var.key)
    if 'value' in data:
        var.value_encrypted = encrypt(data['value'])

    history = VariableHistory(
        variable_id=vid,
        old_value_encrypted=old_enc,
        new_value_encrypted=var.value_encrypted
    )
    session.add(history)
    session.commit()
    session.close()
    return jsonify({'ok': True})


@app.route('/api/variables/<int:vid>', methods=['DELETE'])
def delete_variable(vid):
    session = Session()
    var = session.query(Variable).get(vid)
    if not var:
        session.close()
        return jsonify({'error': 'not found'}), 404
    session.delete(var)
    session.commit()
    session.close()
    return jsonify({'ok': True})


@app.route('/api/variables/<int:vid>/history', methods=['GET'])
def variable_history(vid):
    session = Session()
    entries = session.query(VariableHistory).filter_by(
        variable_id=vid
    ).order_by(VariableHistory.changed_at.desc()).all()
    result = []
    for h in entries:
        result.append({
            'id': h.id,
            'old_value': decrypt(h.old_value_encrypted) if h.old_value_encrypted else None,
            'new_value': decrypt(h.new_value_encrypted),
            'changed_at': h.changed_at.isoformat()
        })
    session.close()
    return jsonify(result)


@app.route('/api/projects/<int:pid>/export', methods=['GET'])
def export_env(pid):
    """Export project variables as .env format"""
    session = Session()
    variables = session.query(Variable).filter_by(project_id=pid).all()
    lines = []
    for v in variables:
        val = decrypt(v.value_encrypted)
        lines.append(f'{v.key}={val}')
    session.close()
    return '\n'.join(lines), 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(debug=True, port=5000)
