# Deploying on Render

The project includes a Render Blueprint in [`render.yaml`](./render.yaml) for a free portfolio demo: a static React site, a FastAPI web service, and a PostgreSQL database. This setup has not been deployed from this workspace.

> **Important: this is a temporary demo, not production hosting.** Render's free PostgreSQL databases have 1 GB of storage, no backups, and expire 30 days after creation. After expiry, the database is inaccessible unless upgraded; after a further 14-day grace period, Render deletes it and its data. Free web services can also spin down when idle. Do not put important or irreplaceable application data in this demo. Review [Render's free-instance limits](https://render.com/docs/free) before creating services.

## 1. Prepare the project repository

The repository root should be the `vite-project` directory containing `render.yaml`, `package.json`, and `backend/`.

1. Create a GitHub repository and push the contents of `vite-project` to it. Render Blueprints require a Git repository connected to Render.
2. Confirm `.env`, `backend/.env`, `.venv/`, `node_modules/`, and build output are not committed. Never commit database credentials or JWT secrets.
3. From the project root, run the frontend checks:

   ```powershell
   npm ci
   npm test
   npm run lint
   npm run build
   npm audit
   ```

4. From `backend`, run the backend checks:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest
   .\.venv\Scripts\python.exe -m pip check
   .\.venv\Scripts\python.exe -m alembic check
   ```

## 2. Create the Render services

1. Sign in to the [Render Dashboard](https://dashboard.render.com/).
2. Choose **New > Blueprint**, connect the GitHub repository, and select the branch to deploy. Set the Blueprint file to `render.yaml` if Render does not detect it automatically.
3. Review the Blueprint before creating services. It selects the free plan for the API and database; the static site is free by default.
4. When Render asks for values for the Blueprint's `sync: false` variables, enter:

   | Service | Variable | Value |
   | --- | --- | --- |
   | API | `CORS_ALLOWED_ORIGINS` | `https://job-application-intelligence-web.onrender.com` |
   | Frontend | `VITE_API_BASE_URL` | `https://job-application-intelligence-api.onrender.com/api/v1` |

   Those addresses match the service names in `render.yaml`. Confirm the actual service URLs after creation. If Render assigns different addresses, update these environment variables in the respective service dashboards and redeploy. The frontend URL is public configuration; it must not contain a secret.

The Blueprint generates `JWT_SECRET_KEY` and connects the API to the database using Render's private database URL. Never copy a database URL or JWT secret into source code or frontend variables.

## 3. Database URL and migrations

Render's PostgreSQL connection URL may begin with `postgres://` or `postgresql://`. The backend and Alembic normalize these forms to SQLAlchemy's `postgresql+psycopg://` driver URL, which matches the installed Psycopg 3 driver.

The free web-service plan does not support Render's pre-deploy command. For this single-instance demo, the Blueprint runs `python -m alembic upgrade head` before Uvicorn each time the API starts. Alembic upgrades are repeatable when the database is already at the current revision. Keep this demo at one API instance; do not use this startup migration pattern for horizontally scaled production services.

For a paid deployment, configure migrations as a pre-deploy command (`python -m alembic upgrade head`) and remove the migration from the start command. Render documents pre-deploy commands as available for paid web services; see [Render deploys](https://render.com/docs/deploys). Back up important data before applying schema changes.

## 4. Verify the deployment

After the Blueprint finishes deploying:

1. Open the API's `/health` URL and confirm it returns `{"status":"ok"}`.
2. Open the API's `/docs` URL and confirm FastAPI's API documentation loads.
3. Visit the frontend URL and register a test account.
4. Create and update an application, then verify dashboard metrics, interviews, follow-ups, and a skill comparison.
5. Refresh the frontend and sign in again. Access tokens are held in memory and are not persisted across refreshes.
6. Check Render logs for migration failures, database connection errors, or CORS rejections.

`/health` only confirms that the API process responds; it does not check the database. The authenticated application workflow and successful migration are the database checks.

The Blueprint configures a rewrite from frontend paths to `/index.html`, so client-side React routes can be refreshed directly. Render supports these rules for static sites; see [static-site rewrites](https://render.com/docs/redirects-rewrites).

## 5. Moving beyond a demo

Before storing data you need to keep, upgrade the PostgreSQL database before the free database expires and verify the upgrade and backup options in Render. A free database has no backups; a CSV export is not a complete database backup. A paid API service avoids the free service's idle spin-down and supports a separate pre-deploy migration command.

The application does not yet include rate limiting, email verification, password reset, server-side token revocation, or database-readiness monitoring. Review those limitations before a public or high-traffic release. No live job-search API or AI provider is configured; job-skill comparisons remain deterministic rules.

Deployment is complete only after a repository is connected, Render services are created, their environment variables and URLs are confirmed, and the deployed workflows above pass.
