# Health Check Endpoints

**Branch**: `019-vercel-deployment`

Each backend service must expose a health check endpoint used for deployment verification.

## Contract

```
GET /api/<service>/health
Authorization: none required
Response: 200 OK  {"status": "ok", "service": "<service-name>"}
```

## Per-Service Endpoints

| Service | Endpoint |
|---------|----------|
| auth-service | `GET /api/auth/health` |
| user-service | `GET /api/users/health` |
| scan-service | `GET /api/scans/health` |
| analytics-service | `GET /api/analytics/health` |
| recommendation-service | `GET /api/recommendations/health` |
| admin-service | `GET /api/admin/health` |

## Quickstart Verification

After deployment, verify all services are alive:

```bash
BASE=https://<your-vercel-domain>.vercel.app
for path in auth/health users/health scans/health analytics/health recommendations/health admin/health; do
  echo -n "$path: "
  curl -s "$BASE/api/$path" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"
done
```

Expected output: `ok` for all six.
