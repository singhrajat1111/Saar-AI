# Commands to Run the SAAR AI Application

## Overview
This document provides the commands to run each part of the SAAR AI application:
- Database (PostgreSQL with pgvector)
- Redis (for WebSocket pub/sub)
- Backend server (FastAPI/Uvicorn)
- Frontend dev server (Next.js)

## Services

### 1. Database (PostgreSQL)
If using Docker/Podman:
```bash
docker run -d --name saarai-db -p 5432:5432 -e POSTGRES_USER=saar -e POSTGRES_PASSWORD=saar -e POSTGRES_DB=saar_db pgvector/pgvector:pg16
```

### 2. Redis (Native Service)
```bash
# On Linux with systemd
sudo systemctl start redis

# Or manually
redis-server
```

### 3. Backend Server
From the `/home/rajatsingh/Desktop/Saar-AI/backend` directory:
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```
For development with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

### 4. Frontend Dev Server
From the `/home/rajatsingh/Desktop/Saar-AI/frontend` directory:
```bash
npm run dev
```

## Notes
- Ensure the `.env` file is configured with the correct `REDIS_URL` and database connection string.
- The application no longer uses Celery; all processing happens synchronously within the API request.
- WebSocket updates are still powered by Redis pub/sub, so Redis must be running.
