<p align="center">
  <img src="assets/banner.svg" alt="KitabGhar Exchange APIs" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLModel-ORM-E3452B?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLModel">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Uvicorn-ASGI-2094F3?style=flat-square" alt="Uvicorn">
  <img src="https://img.shields.io/badge/managed%20with-uv-DE5FE9?style=flat-square&logo=uv&logoColor=white" alt="uv">
  <img src="https://img.shields.io/badge/OpenAPI-3.1-6BA539?style=flat-square&logo=openapiinitiative&logoColor=white" alt="OpenAPI">
  <img src="https://img.shields.io/badge/API-v1.0.0-blue?style=flat-square" alt="API version 1.0.0">
  <img src="https://img.shields.io/github/license/Zain-Ahma12/KitabGhar?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/last-commit/Zain-Ahma12/KitabGhar?style=flat-square" alt="Last commit">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs welcome">
</p>

---

## <img src="assets/icons/book.svg" width="32" height="32" align="absmiddle"> About

**KitabGhar** (Hindi for *"house of books"*) is a REST API for a small book-lending service. It tries to mimic the **book rental system in the real world**: a library keeps a catalogue of books, registered members borrow them for a fixed period, and the books come back to the shelf when they are returned.

Every book is always in exactly one state, and the API enforces it:

- <img src="assets/icons/status-available.svg" width="18" height="18" align="absmiddle" alt="Available"> **Available**: on the shelf and ready to be borrowed.
- <img src="assets/icons/status-borrowed.svg" width="18" height="18" align="absmiddle" alt="Borrowed"> **Borrowed**: held by one registered user, with a start date and an end date.
- <img src="assets/icons/status-removed.svg" width="18" height="18" align="absmiddle" alt="Removed"> **Removed**: taken out of circulation, with a removal date.

A book cannot be borrowed twice, a borrowed book cannot be removed before it is returned, and a user who still holds books cannot be deleted. Built with FastAPI and SQLModel, with automatic validation and OpenAPI docs.

---

## <img src="assets/icons/rocket.svg" width="32" height="32" align="absmiddle"> How to Run

**1. Install `uv`**

```bash
pip install uv
```

**2. Clone the repository**

```bash
git clone https://github.com/Zain-Ahma12/KitabGhar.git
cd KitabGhar
```

**3. Create `.env` file** using **`.env.example`**
```bash
cp .env.example .env
```

> `X-API-KEY` is the secret that clients must send in the `x-api-key` header for the protected endpoints (see [API Endpoints](#api-endpoints)).

**4. Start the server.** `uv` creates the virtual environment and installs every dependency for you:

```bash
uv run main.py
```

The API is now running at **http://127.0.0.1:8000**. Tables are created automatically on startup.

| What | Where |
| --- | --- |
| Interactive docs | http://127.0.0.1:8000/docs |
| Health check | http://127.0.0.1:8000/health |

---

## <img src="assets/icons/folder.svg" width="32" height="32" align="absmiddle"> Folder Structure

```text
KitabGhar/
├── .venv/                  # Virtual environment created by uv
├── custom_docs_ui/         # Custom Swagger UI
│   ├── __pycache__/
│   ├── __init__.py
│   └── docs_ui.py          # setup_custom_docs(): dark mode, animation, typography
├── assets/                 # contains svg graphics for the animation in Readme
├── models/                 # SQLModel tables, request/response schemas, business rules
│   ├── __pycache__/
│   ├── __init__.py
│   ├── books.py            # Book table, book states, borrow/return/remove helpers
│   └── users.py            # User table and conversion helpers
├── routes/                 # FastAPI routers
│   ├── __pycache__/
│   ├── __init__.py
│   ├── book_routes.py      # /book endpoints
│   └── users_routes.py     # /user endpoints
├── .env.example            # copy of .env file for github
├── .gitignore
├── .python-version         # Python version used by uv
├── auth.py                 # x-api-key verification dependency
├── database.py             # Engine, table creation and session provider
├── KitabGhar.db            # SQLite database file
├── main.py                 # App entry point, lifespan, /health
├── pyproject.toml          # Project metadata and dependencies
├── README.md
├── uv.lock                 # Locked dependency versions
├── CONTRIBUTING.md         # Read this before contributing to this project
└── LICENSE.md              # MIT License
```

---

<a id="api-endpoints"></a>

## <img src="assets/icons/api.svg" width="32" height="32" align="absmiddle"> API Endpoints

<p align="center">
  <img src="assets/api-architecture.svg" alt="Request flow: client to Uvicorn server to the book, user and health endpoints, then to the SQLite database" width="100%">
</p>

Every request travels from the client to **Uvicorn**, which hands it to the **FastAPI** app. FastAPI validates it, routes it to the right endpoint, and the endpoint reads or writes the **SQLite** database through SQLModel.

### <img src="assets/icons/books.svg" width="28" height="28" align="absmiddle"> Books `/book`

| Method | Endpoint | Description | Auth |
| :---: | --- | --- | :---: |
| `POST` | `/book/new` | Add a new book (starts as available) | <img src="assets/icons/lock.svg" width="22" height="22" alt="Requires x-api-key"> |
| `GET` | `/book/all` | List all books. Filters: `book_name`, `author`, `publish_year` (name and author are partial matches) | |
| `GET` | `/book/available` | List books that can be borrowed right now | |
| `GET` | `/book/borrowed` | List borrowed books with borrower and dates | |
| `GET` | `/book/borrowers_info` | Borrowed books grouped by borrower | |
| `GET` | `/book/{book_id}` | Get one book | |
| `PATCH` | `/book/{book_id}` | Update name, author, year or condition | |
| `POST` | `/book/{book_id}/borrow` | Borrow a book for an existing user | |
| `POST` | `/book/{book_id}/return` | Return a borrowed book | |

The list endpoints are paginated with `page` (default `1`) and `page_size` (default `10`, max `100`).

### <img src="assets/icons/user.svg" width="28" height="28" align="absmiddle"> Users `/user`

| Method | Endpoint | Description | Auth |
| :---: | --- | --- | :---: |
| `POST` | `/user/register` | Register a new user (email must be unique) | <img src="assets/icons/lock.svg" width="22" height="22" alt="Requires x-api-key"> |
| `GET` | `/user/all` | List all users | |
| `GET` | `/user/{user_id}` | Get one user | |
| `PATCH` | `/user/{user_id}` | Update a user | |
| `DELETE` | `/user/{user_id}` | Delete a user (blocked while they hold books) | <img src="assets/icons/lock.svg" width="22" height="22" alt="Requires x-api-key"> |

### <img src="assets/icons/pulse.svg" width="28" height="28" align="absmiddle"> Health

| Method | Endpoint | Description |
| :---: | --- | --- |
| `GET` | `/health` | Liveness check with uptime. Never touches the database |

### <img src="assets/icons/lock.svg" width="28" height="28" align="absmiddle"> Authentication

Endpoints marked with <img src="assets/icons/lock.svg" width="18" height="18" align="absmiddle" alt="lock"> require the `x-api-key` header to match the `X-API-KEY` value in your `.env` file. A wrong or missing key is rejected with `401 Unauthorized`.

```bash
curl -X POST http://127.0.0.1:8000/book/new \
  -H "Content-Type: application/json" \
  -H "x-api-key: replace-with-a-long-random-string" \
  -d '{"book_name": "The Guide", "author": "R. K. Narayan", "published_year": 1958}'
```

---

## <img src="assets/icons/moon.svg" width="32" height="32" align="absmiddle"> Custom Swagger UI

FastAPI's default `/docs` page is functional, but I wanted something that felt better to work in. So I built my own Swagger UI in the [`custom_docs_ui`](custom_docs_ui/) package. The default docs route is switched off in `main.py` and replaced with `setup_custom_docs(app, docs_path="/docs")`.

What it adds on top of the stock UI:

- **Dark mode** for comfortable reading at any hour.
- **Animations** that make the page feel smoother and more alive.
- **Updated typography** for a cleaner, more readable interface.

It is still the same OpenAPI-powered "Try it out" experience, just nicer to use. Start the server and open `/docs` to see it.

### Demo Video

[▶ Watch the Swagger UI Demo](https://zain-ahma12.github.io/Rangmanch-Review-api/)<!-- Add a screenshot: ![Custom Swagger UI](assets/swagger-ui.png) -->

---

## <img src="assets/icons/heart.svg" width="32" height="32" align="absmiddle"> Contributing & License

Contributions are welcome, whether it is a bug report, a new feature or a small docs fix. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for how to set up the project and open a pull request.

This project is licensed under the terms of the [LICENSE](LICENSE) file.

Thank you