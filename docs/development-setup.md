# Development Setup

This guide sets up a local UniFlow development environment. UniFlow uses **native installs only**, with no Docker. Sections are added as the foundation tasks (M0) land.

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Git | recent | `git --version` |
| Python | 3.12+ | `python --version` |
| Node.js | current LTS | `node --version` |
| MySQL Server | 8.x (8.4 LTS recommended) | `mysql --version` |

## 1. Local database

UniFlow does not ship a database setup script. Create the database yourself in your local MySQL server, using any client you like: the `mysql` CLI, MySQL Workbench or similar.

Requirements:

- **Database name `uniflow`**, using `utf8mb4`. This is the MySQL 8 default, but being explicit does no harm:

  ```sql
  CREATE DATABASE uniflow CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
  ```

- **The MySQL account Django uses must be able to create and drop `test_uniflow`.** pytest creates this test database on every run, starting in M0.5. `root` already can. If you use a dedicated user, grant it `ALL` on both `uniflow.*` and `test_uniflow.*`.

Django connects to the database through the settings in `backend/.env` (M0.4): `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`. That file is never committed.
