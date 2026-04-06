# Data Model: Deploy App to Vercel

**Branch**: `019-vercel-deployment`  
**Date**: 2026-04-06

## No Database Schema Changes

This feature is purely deployment configuration. No tables, columns, or migrations are added or modified.

---

## Files Created or Modified

### New Files

| File | Purpose |
|------|---------|
| `vercel.json` (root, replace existing) | Vercel build + routing config with includeFiles, maxDuration, Python version |
| `frontend/.env.production` | Documents production env var values (NEXT_PUBLIC_* = empty string); committed to repo as documentation |
| `DEPLOYMENT.md` (root) | Step-by-step guide for connecting GitHub to Vercel, setting env vars, and verifying deployment |

### Modified Files

| File | Change |
|------|--------|
| `vercel.json` (existing root file) | Add `config.includeFiles` for shared lib + requirements.txt; add `maxDuration`; add `functions` block for Python 3.11 (Vercel's max supported) |
| `services/*/src/main.py` (all 6) | Add health-check endpoint `GET /api/<service>/health` returning `{"status": "ok"}` — used for deployment verification |

---

## Environment Variable Reference

All environment variables required for the deployed app. These are set in the Vercel dashboard (never committed to the repo).

### Frontend Variables (set as Vercel Environment Variables → Production)

| Variable | Production Value | Sensitivity |
|----------|----------------|-------------|
| `NEXT_PUBLIC_AUTH_URL` | `""` (empty) | Public |
| `NEXT_PUBLIC_USER_URL` | `""` (empty) | Public |
| `NEXT_PUBLIC_SCAN_URL` | `""` (empty) | Public |
| `NEXT_PUBLIC_ANALYTICS_URL` | `""` (empty) | Public |
| `NEXT_PUBLIC_RECOMMENDATION_URL` | `""` (empty) | Public |
| `NEXT_PUBLIC_ADMIN_URL` | `""` (empty) | Public |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | OAuth2 client ID | Public |

### Backend Variables (set as Vercel Environment Variables → Production, all services)

| Variable | Description | Sensitivity |
|----------|-------------|-------------|
| `DATABASE_URL` | Supabase PostgreSQL async connection string | **Secret** |
| `JWT_SECRET` | JWT signing key (shared across services) | **Secret** |
| `SUPABASE_URL` | Supabase project API URL | **Secret** |
| `SUPABASE_KEY` | Supabase service role key | **Secret** |

### Service-Specific Backend Variables

| Variable | Service | Description | Sensitivity |
|----------|---------|-------------|-------------|
| `GEMINI_API_KEY` | recommendation-service | Google Gemini API key | **Secret** |
| `SUPABASE_STORAGE_BUCKET` | scan-service | Supabase storage bucket name | Public |
