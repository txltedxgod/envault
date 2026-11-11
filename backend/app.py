import os
import re
from contextlib import contextmanager

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

try:
    from .crypto import decrypt, encrypt
    from .models import Base, Project, Variable, VariableHistory
except ImportError:
    from crypto import decrypt, encrypt
    from models import Base, Project, Variable, VariableHistory

_ENV_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.-]*$')


def _format_env_line(key: str, value: str) -> str:
    if any(ch in value for ch in ('\n', '\r', '"', '#', ' ', '\t')) or value == '':
        escaped = (
            value.replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
        )
        return f'{key}="{escaped}"'
    return f'{key}={value}'


def create_app(database_url: str | None = None) -> Flask:
    flask_app = Flask(__name__)
    CORS(flask_app)

    db_url = database_url or os.getenv('ENVAULT_DATABASE_URL', 'sqlite:///envault.db')
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    @contextmanager
    def session_scope():
        session = session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @flask_app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'})

    @flask_app.route('/api/projects', methods=['GET'])
    def list_projects():
        with session_scope() as session:
            projects = session.query(Project).order_by(Project.created_at.desc()).all()
            return jsonify([
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'var_count': len(p.variables),
                    'created_at': p.created_at.isoformat(),
                }
                for p in projects
            ])

    @flask_app.route('/api/projects', methods=['POST'])
    def create_project():
        data = request.get_json(silent=True) or {}
        name = str(data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'project name is required'}), 400

        description = str(data.get('description') or '').strip()
        with session_scope() as session:
            project = Project(name=name, description=description)
            session.add(project)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return jsonify({'error': 'project already exists'}), 409
            return jsonify({'id': project.id, 'name': project.name}), 201

    @flask_app.route('/api/projects/<int:pid>', methods=['DELETE'])
    def delete_project(pid: int):
        with session_scope() as session:
            project = session.get(Project, pid)
            if not project:
                return jsonify({'error': 'not found'}), 404
            session.delete(project)
            session.commit()
            return jsonify({'ok': True})

    @flask_app.route('/api/projects/<int:pid>/variables', methods=['GET'])
    def list_variables(pid: int):
        with session_scope() as session:
            project = session.get(Project, pid)
            if not project:
                return jsonify({'error': 'project not found'}), 404
            variables = session.query(Variable).filter_by(project_id=pid).order_by(Variable.id.asc()).all()
            return jsonify([
                {
                    'id': v.id,
                    'key': v.key,
                    'value': decrypt(v.value_encrypted),
                    'updated_at': v.updated_at.isoformat(),
                }
                for v in variables
            ])

    @flask_app.route('/api/projects/<int:pid>/variables', methods=['POST'])
    def add_variable(pid: int):
        data = request.get_json(silent=True) or {}
        key = str(data.get('key') or '').strip()
        if not key or not _ENV_KEY_RE.match(key):
            return jsonify({'error': 'valid variable key is required'}), 400
        if 'value' not in data or data['value'] is None:
            return jsonify({'error': 'variable value is required'}), 400
        raw_value = str(data['value'])

        with session_scope() as session:
            project = session.get(Project, pid)
            if not project:
                return jsonify({'error': 'project not found'}), 404

            var = Variable(
                project_id=pid,
                key=key,
                value_encrypted=encrypt(raw_value),
            )
            session.add(var)
            session.flush()

            history = VariableHistory(
                variable_id=var.id,
                new_value_encrypted=var.value_encrypted,
            )
            session.add(history)
            session.commit()
            return jsonify({'id': var.id, 'key': var.key}), 201

    @flask_app.route('/api/variables/<int:vid>', methods=['PUT'])
    def update_variable(vid: int):
        data = request.get_json(silent=True) or {}
        with session_scope() as session:
            var = session.get(Variable, vid)
            if not var:
                return jsonify({'error': 'not found'}), 404

            old_enc = var.value_encrypted
            if 'key' in data:
                new_key = str(data.get('key') or '').strip()
                if not new_key or not _ENV_KEY_RE.match(new_key):
                    return jsonify({'error': 'valid variable key is required'}), 400
                var.key = new_key

            if 'value' in data and data['value'] is not None:
                var.value_encrypted = encrypt(str(data['value']))

            history = VariableHistory(
                variable_id=vid,
                old_value_encrypted=old_enc,
                new_value_encrypted=var.value_encrypted,
            )
            session.add(history)
            session.commit()
            return jsonify({'ok': True})

    @flask_app.route('/api/variables/<int:vid>', methods=['DELETE'])
    def delete_variable(vid: int):
        with session_scope() as session:
            var = session.get(Variable, vid)
            if not var:
                return jsonify({'error': 'not found'}), 404
            session.delete(var)
            session.commit()
            return jsonify({'ok': True})

    @flask_app.route('/api/variables/<int:vid>/history', methods=['GET'])
    def variable_history(vid: int):
        with session_scope() as session:
            var = session.get(Variable, vid)
            if not var:
                return jsonify({'error': 'not found'}), 404
            entries = (
                session.query(VariableHistory)
                .filter_by(variable_id=vid)
                .order_by(VariableHistory.changed_at.desc(), VariableHistory.id.desc())
                .all()
            )
            return jsonify([
                {
                    'id': h.id,
                    'old_value': decrypt(h.old_value_encrypted) if h.old_value_encrypted else None,
                    'new_value': decrypt(h.new_value_encrypted),
                    'changed_at': h.changed_at.isoformat(),
                }
                for h in entries
            ])

    @flask_app.route('/api/projects/<int:pid>/export', methods=['GET'])
    def export_env(pid: int):
        """Export project variables as .env format."""
        with session_scope() as session:
            project = session.get(Project, pid)
            if not project:
                return jsonify({'error': 'project not found'}), 404
            variables = session.query(Variable).filter_by(project_id=pid).order_by(Variable.id.asc()).all()
            lines = [_format_env_line(v.key, decrypt(v.value_encrypted)) for v in variables]
            return '\n'.join(lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}

    return flask_app


app = create_app()


if __name__ == '__main__':
    app.run(debug=os.getenv('ENVAULT_DEBUG') == '1', port=5000)
