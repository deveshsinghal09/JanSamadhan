# Deployment guide

This guide documents the production layout used by the hosted JanSamadhan
prototype.

## Services

- **Render:** one Docker web service containing the Express API and private
  FastAPI inference process
- **Neon:** PostgreSQL for users, complaints, history, and uploaded image bytes
- **Vercel:** static Vite frontend with a same-origin rewrite from `/api/*` to
  Render

## Required secret

`DATABASE_URL` is the only required production secret. Set it in Render's
environment settings. Do not put the real connection string in `render.yaml`,
`vercel.json`, a Git commit, a screenshot, or an issue.

## Render

The root `render.yaml` defines a Singapore-region Docker web service on the
free plan. The container:

1. Builds the Vite frontend.
2. Installs production Node dependencies.
3. Creates a Python virtual environment and installs CPU PyTorch.
4. Starts FastAPI on container-local port 8001.
5. Starts Express on Render's public `PORT`.

The health endpoint is `/api/health`. A healthy response reports
`ai: true`, `database: true`, and `storage: "Neon PostgreSQL"`.

The first build can take several minutes because the image includes PyTorch.
Render free services can sleep when idle and may need a cold start.

## Vercel

The Vercel project builds with `npm run build` and publishes `dist`.
`vercel.json` forwards API traffic to the deployed Render origin. This keeps
browser requests and the session cookie on the Vercel hostname.

When the Render hostname changes, update the rewrite destination and redeploy
Vercel.

## Post-deployment checks

1. Open `/api/health` and confirm the AI and database fields.
2. Register a new citizen account.
3. Sign in and submit a text-only report.
4. Submit a report with a JPEG or PNG photo.
5. Sign in as the relevant officer and move the report to In Progress.
6. Sign in as administrator and verify reassignment and priority changes.
7. Confirm the submitted report remains after a redeploy.

## Rollback

Both platforms deploy from Git commits. Restore the last known-good deployment
from the provider dashboard or revert the faulty Git commit. Database changes
are additive and initialized by [`backend/postgres.js`](../backend/postgres.js).
