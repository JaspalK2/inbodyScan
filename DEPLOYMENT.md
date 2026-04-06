# Deployment Guide — InBody Scan Analyzer

This guide covers deploying the full application (Next.js frontend + 6 FastAPI backend services) to Vercel as a unified monorepo project.

> **Note**: Claude Code cannot access live Vercel URLs remotely. All bug fixes still happen via local code changes pushed to GitHub, which trigger automatic redeployments.

---

## Architecture

Everything deploys to a single Vercel project:

- **Frontend** (`/`) → Next.js 15, built with `@vercel/next`
- **Auth API** (`/api/auth/*`) → `services/auth-service` (Python 3.12, FastAPI + Mangum)
- **User API** (`/api/users/*`) → `services/user-service`
- **Scan API** (`/api/scans/*`) → `services/scan-service`
- **Analytics API** (`/api/analytics/*`) → `services/analytics-service`
- **Recommendations API** (`/api/recommendations/*`) → `services/recommendation-service`
- **Admin API** (`/api/admin/*`) → `services/admin-service`

Since frontend and APIs share the same domain, there are no CORS issues.

---

## Step 1: Connect GitHub Repo to Vercel (One-Time Manual Step)

1. Go to [vercel.com/new](https://vercel.com/new) and sign in
2. Click **Import Git Repository** → select `JaspalK2/inbodyScan`
3. **Root Directory**: leave as `/` (the `vercel.json` at root handles routing)
4. **Framework Preset**: Other
5. Click **Deploy** — the first deploy may fail (env vars not set yet); that's OK

---

## Step 2: Set Environment Variables

In your Vercel project: **Settings → Environment Variables → Add**

Set all variables for **Production** environment.

### Frontend Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_AUTH_URL` | *(empty string)* | Same-origin — leave blank |
| `NEXT_PUBLIC_USER_URL` | *(empty string)* | Same-origin — leave blank |
| `NEXT_PUBLIC_SCAN_URL` | *(empty string)* | Same-origin — leave blank |
| `NEXT_PUBLIC_ANALYTICS_URL` | *(empty string)* | Same-origin — leave blank |
| `NEXT_PUBLIC_RECOMMENDATION_URL` | *(empty string)* | Same-origin — leave blank |
| `NEXT_PUBLIC_ADMIN_URL` | *(empty string)* | Same-origin — leave blank |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | `926220032336-...` | Your Google OAuth client ID |

> **Why empty string?** All services are on the same domain, so `/api/auth/login` resolves correctly without a base URL.

### Backend Variables (All Services)

| Variable | Description | Where to find it |
|----------|-------------|-----------------|
| `DATABASE_URL` | Supabase PostgreSQL async URL | Supabase → Settings → Database → Connection string (use `postgresql+asyncpg://...`) |
| `JWT_SECRET` | JWT signing secret | Generate with `openssl rand -hex 32` |
| `SUPABASE_URL` | Supabase project URL | Supabase → Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase service role key | Supabase → Settings → API → service_role key |

### Service-Specific Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | recommendation-service | Google AI Studio API key |
| `SUPABASE_STORAGE_BUCKET` | scan-service | Supabase storage bucket name for scan uploads |

> ⚠️ **Never commit actual secret values** to the repository. The `.env.local` file is gitignored.

---

## Step 3: Redeploy

After setting environment variables:

1. Go to **Deployments** in your Vercel project
2. Click the most recent deployment → **Redeploy**
3. Wait ~2–5 minutes for the build to complete

---

## Step 4: Verify Health Endpoints

Once deployed, verify all 6 services are running:

```bash
BASE=https://your-project.vercel.app

for path in auth/health users/health scans/health analytics/health recommendations/health admin/health; do
  echo -n "  $path: "
  curl -s "$BASE/api/$path" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"
done
```

Expected output:
```
  auth/health: ok
  users/health: ok
  scans/health: ok
  analytics/health: ok
  recommendations/health: ok
  admin/health: ok
```

---

## Step 5: Smoke Test

1. Open `https://your-project.vercel.app` in a browser
2. Register a new account or log in with an existing account
3. Upload an InBody scan (CSV or PDF)
4. Navigate to **Recommendations** → **Generate Diet Plan**
5. Verify a 7-day plan appears with meals and macros

---

## Automatic Redeployments

Any push to the `main` branch automatically triggers a new Vercel deployment. Pull requests get preview deployments at unique URLs.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Frontend loads but API calls fail | `NEXT_PUBLIC_*_URL` not set to empty string | Set all 6 to empty string `""` in Vercel env vars |
| `500 Internal Server Error` on any endpoint | Missing secret env var | Check Vercel → Functions → Logs for the specific error |
| Health endpoint returns 404 | Route not matching | Verify `vercel.json` routes include `/api/<service>/(.*)` |
| Build fails: `No module named 'shared'` | `includeFiles` not bundling shared library | Verify `vercel.json` includes `"shared/**"` in each build's `includeFiles` |
| Recommendation service times out | Plan generation exceeds default timeout | Verify `maxDuration: 30` is set for recommendation-service in `vercel.json` |
| Function size limit exceeded | Large ML dependencies | See note below about recommendation-service size |

### Recommendation Service Size

The `recommendation-service` includes `google-generativeai` and `groq` which are large packages. If the Vercel build fails with a size limit error:

1. Check the build output for the function size
2. If over 250MB, deploy `recommendation-service` separately to [Railway](https://railway.app) (free tier)
3. Set `NEXT_PUBLIC_RECOMMENDATION_URL=https://your-railway-app.railway.app` in Vercel env vars

---

## Local Development (Unchanged)

Local development is unaffected. Keep using `.env.local` with `localhost:800X` URLs and start services with `./start-local.sh`.
