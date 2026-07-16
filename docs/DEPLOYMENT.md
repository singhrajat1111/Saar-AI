# Deployment

This repo is set up for:

- Backend API + Celery worker on Render
- Redis on Render
- Frontend on Vercel

The first production deployment runs the backend API and Celery worker in the same Render web service so they share the same persistent disk for uploaded datasets.

## Backend on Render

1. Push the repo to GitHub.
2. In Render, create a new Blueprint from `render.yaml`.
3. Set `CORS_ORIGINS` to your Vercel frontend URL, for example:

```text
https://saar-ai.vercel.app
```

4. Optional: set `GEMINI_API_KEY` or `OPENAI_API_KEY`. If omitted, SAAR uses the local rule-based explanation fallback.
5. Render provisions:
   - `saar-ai-redis`
   - `saar-ai-backend`
   - persistent disk mounted at `/var/data/saar-ai`

Backend health check:

```text
https://<render-backend-url>/health
```

Expected response:

```json
{"status":"ok","service":"saar_ai_backend"}
```

## Frontend on Vercel

1. Import the same GitHub repo in Vercel.
2. Set the Vercel project root directory to `frontend`.
3. Add environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-backend-url>
NEXT_PUBLIC_WS_BASE_URL=wss://<render-backend-url>
```

4. Deploy.

## Required Production Smoke Test

After both services deploy, test:

1. Open the Vercel URL.
2. Upload a normal CSV. It should complete the analysis pipeline.
3. Upload `unicode.csv`. It should pass validation.
4. Upload an emoji-only header CSV:

```csv
😀,🚀,💰
1,2,3
4,5,6
```

Expected: validation fails gracefully with `INVALID_HEADER_CHARACTERS`.

5. Upload an empty CSV.

Expected: validation fails gracefully with `EMPTY_FILE` and no HTTP 500.

## Notes

- Do not commit runtime files from `storage/`.
- For higher-scale production, move uploaded files from local disk to object storage such as S3, Cloudflare R2, or Supabase Storage, then run API and Celery as separate services.
