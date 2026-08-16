# envault

> Secure environment variable manager for teams with AES-128 encryption, version history, and React UI.

[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite)](https://vitejs.dev)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Cryptography](https://img.shields.io/badge/Fernet-AES--128-green?style=flat-square)](https://cryptography.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

`#env-manager` `#secrets-management` `#react` `#vite` `#flask` `#encryption` `#developer-tools`

---

## Features

- **Project Grouping:** Separate environment variables by project and environment.
- **Encrypted at Rest:** All secret values are symmetrically encrypted using Fernet (AES-128-CBC + HMAC).
- **Audit & Version History:** Track changes and previous values for every variable.
- **Export to `.env`:** One-click download of project configs as ready-to-use `.env` files.
- **Show/Hide Toggle:** Protect sensitive API keys and secrets from screen peering.

## Quick Start

### Docker Compose

```bash
docker compose up --build
```

Access frontend at `http://localhost:3000` (API running on `http://localhost:5000`).

### Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd ../frontend
npm install
npm run dev
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a project |
| `DELETE` | `/api/projects/:id` | Delete project |
| `GET` | `/api/projects/:id/variables` | Get decrypted variables for project |
| `POST` | `/api/projects/:id/variables` | Add variable to project |
| `PUT` | `/api/variables/:id` | Update variable key/value |
| `DELETE` | `/api/variables/:id` | Delete variable |
| `GET` | `/api/variables/:id/history` | Get revision history for variable |
| `GET` | `/api/projects/:id/export` | Download `.env` formatted plain text |
