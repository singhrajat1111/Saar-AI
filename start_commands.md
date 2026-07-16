redis- docker compose up -d

backend- source venv/bin/activate
uvicorn main:app --reload --port 8000

frontend- npm run dev

celery worker-  source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info




The Whole Process to Get Everything Running
Once you select that image, here is the complete sequence of commands to get the entire application running:

1. Start the Database (Podman)
Ensure the database container is started by selecting docker.io/pgvector/pgvector:pg16. If it finishes, it will run in the background.

2. Start Redis (Native Service)
You already set this up, but ensure it is running:

bash
sudo systemctl start redis
3. Start the Backend Server (Terminal 1)
From the /home/rajatsingh/Desktop/Saar-AI/backend directory:

bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
4. Start the Celery Worker (Terminal 2)
From the /home/rajatsingh/Desktop/Saar-AI/backend directory:


source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
5. Start the Frontend Dev Server (Terminal 3)
From the /home/rajatsingh/Desktop/Saar-AI/frontend directory:

npm run dev