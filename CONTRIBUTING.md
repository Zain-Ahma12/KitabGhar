# Contributing to KitabGhar

Thanks for your interest in KitabGhar! Bug reports, feature ideas, docs fixes and code contributions are all welcome. This guide explains how to get set up and what a good contribution looks like.

## Ways to contribute

- **Report a bug.** Open an issue with the steps to reproduce it, what you expected, and what actually happened. Include the request you sent and the response or traceback if you have them.
- **Suggest a feature.** Open an issue and describe the problem you want to solve before proposing a solution. Ideas that fit the "real-world book rental" theme are the best fit.
- **Improve the docs.** Typos, unclear steps and missing examples are all worth fixing.
- **Send code.** Pick an open issue or open one first, so we can agree on the approach before you invest time.

## Getting started

1. **Fork** the repository and clone your fork:

   ```bash
   git clone https://github.com/Zain-Ahma12/KitabGhar.git
   cd KitabGhar
   ```

2. **Install `uv`** if you do not have it:

   ```bash
   pip install uv
   ```

3. **Create `.env` file** using **`.env.example`**
   ```bash
   cp .env.example .env
   ```

4. **Run the app.** `uv` creates the virtual environment and installs the dependencies:

   ```bash
   uv run main.py
   ```

   The server starts on http://127.0.0.1:8000 with auto-reload, and the docs are at `/docs`.

5. **Create a branch** for your work:

   ```bash
   git checkout -b feat/short-description
   ```

   Suggested prefixes: `feat/`, `fix/`, `docs/`, `refactor/`.

## Project conventions

Please follow the patterns already in the codebase.

- **Where code goes.** Database tables, request and response schemas, and business rules live in `models/`. Route handlers live in `routes/`. Keep handlers thin and put reusable logic in model helpers.
- **Separate schemas from tables.** Each resource has a table model (`Book`, `User`) and separate `Create`, `Update` and `Read` models. Never return a table model directly from an endpoint. Convert it with the `*_to_read` helpers.
- **Keep book states valid.** A book is exactly one of available, borrowed or removed. Any change to a book should pass through `validate_book_state()` before it is committed.
- **Handle errors with `HTTPException`.** Use the right status code (`404` for missing records, `409` for conflicts, `400` for invalid operations) and a clear `detail` message. Roll back the session when a change is rejected.
- **Protect write endpoints deliberately.** Endpoints that create or delete important records use the `verify_api_key` dependency. If you add a similar endpoint, decide whether it should be protected too.
- **Write readable Python.** Use type hints, short docstrings on functions, and descriptive names. Follow the existing style and keep functions small.
- **Mind the database.** Avoid loading related rows one by one in a loop. The existing endpoints use `selectinload` for this reason.
- **Never commit secrets.** `.env` and local database files must stay out of git.

If you change a table, mention it in your pull request. The app creates missing tables on startup but does not migrate existing ones, so a schema change may require recreating your local database.

## Commit messages

Write short, present-tense messages that say what changed:

```text
feat: add endpoint to extend a borrowing period
fix: reject borrow requests for removed books
docs: clarify the .env setup
```

## Opening a pull request

Before you open a pull request, check that:

- [ ] The app starts with `uv run main.py` and your change works at `/docs`.
- [ ] You tried the failure cases too, not just the happy path.
- [ ] New or changed endpoints have a docstring, since it appears in the Swagger UI.
- [ ] The README is updated if you changed the setup, the endpoints or the folder structure.
- [ ] The pull request is focused on one change.

In the description, explain **what** you changed and **why**, and link the related issue (for example, `Closes #12`). Small, focused pull requests are reviewed much faster than large ones.

## Code of conduct

Be kind and respectful. Assume good intent, give constructive feedback, and keep discussions about the work. Harassment or discrimination of any kind will not be tolerated.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project. See the [LICENSE](LICENSE) file.
