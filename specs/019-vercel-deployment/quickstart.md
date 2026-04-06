# Quickstart / Deployment Verification

**Branch**: `019-vercel-deployment`  
**Date**: 2026-04-06

---

## Step 1: Connect GitHub Repo to Vercel (One-Time Manual Step)

This step CANNOT be automated from code — it requires the Vercel dashboard.

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import `JaspalK2/inbodyScan` from GitHub
3. **Root directory**: leave as `/` (the `vercel.json` at root handles everything)
4. **Framework preset**: Other (not Next.js — the vercel.json handles it)
5. Click Deploy — the first deploy will likely fail (env vars not set yet) — that's OK

---

## Step 2: Set Environment Variables in Vercel Dashboard

Go to your Vercel project → Settings → Environment Variables. Add all variables from `data-model.md`. Set them for **Production** (and optionally Preview).

**Critical**: Set all six `NEXT_PUBLIC_*_URL` to **empty string `""`** (not localhost, not the Vercel domain — empty string).

---

## Step 3: Redeploy

In Vercel → Deployments → click the latest deployment → Redeploy. This picks up the new env vars.

---

## Step 4: Verify Health Endpoints

```bash
BASE=https://<your-project>.vercel.app

curl $BASE/api/auth/health
# Expected: {"status":"ok","service":"auth"}

curl $BASE/api/users/health
curl $BASE/api/scans/health
curl $BASE/api/analytics/health
curl $BASE/api/recommendations/health
curl $BASE/api/admin/health
```

All should return `200 {"status":"ok"}`.

---

## Step 5: End-to-End Smoke Test

1. Open `https://<your-project>.vercel.app` in a browser
2. Register a new account or log in
3. Upload a scan (CSV or PDF)
4. Navigate to Recommendations → Generate Diet Plan
5. Verify a 7-day plan appears with meals

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Frontend loads but API calls fail (CORS) | This shouldn't happen (same-origin). Check browser console for the actual URL being called | Verify NEXT_PUBLIC_*_URL = empty string |
| 500 on any API endpoint | Missing environment variable (DATABASE_URL, JWT_SECRET, etc.) | Check Vercel Functions logs for the specific error |
| `Module not found: shared` | includeFiles not pulling in shared library | Verify vercel.json includeFiles paths |
| Recommendation service timeout | Plan generation exceeds default 10s limit | Verify maxDuration=30 is set in vercel.json |
| Build fails on scan-service | PyMuPDF or boto3 too large | Check function size in build output |

---

## Local Development (unchanged)

Nothing changes for local development. `.env.local` still has `localhost:800X` URLs and all services still run via uvicorn locally.
