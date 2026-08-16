# envault

Secure environment variable manager for teams. Store, encrypt, version, and share `.env` files across projects.

## Features

- Create projects and manage env variables
- All values encrypted at rest (Fernet symmetric encryption)
- Version history for each variable
- Export as `.env` file
- Show/hide values toggle
- React frontend with dark UI

## Architecture

```
frontend/     React + Vite
backend/      Flask + SQLAlchemy + SQLite
```

## Setup

### With Docker

```bash
docker compose up --build
```

### Manual

```bash
# backend
cd backend
pip install -r requirements.txt
python app.py

# frontend
cd frontend
npm install
npm run dev
```

Backend runs on :5000, frontend on :3000 (proxies API requests).

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/projects | List projects |
| POST | /api/projects | Create project |
| DELETE | /api/projects/:id | Delete project |
| GET | /api/projects/:id/variables | List variables (decrypted) |
| POST | /api/projects/:id/variables | Add variable |
| PUT | /api/variables/:id | Update variable |
| DELETE | /api/variables/:id | Delete variable |
| GET | /api/variables/:id/history | Variable change history |
| GET | /api/projects/:id/export | Export as .env text |

## Security

Values are encrypted with Fernet (AES-128-CBC). The key is generated on first run and stored in `backend/.secret.key`. Keep this file safe.

## TODO

- [ ] user auth
- [ ] import .env file
- [ ] team sharing with access control
