import os
import ssl
from dotenv import load_dotenv
load_dotenv()

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL environment variable is required. Configure Upstash Redis before starting SAAR AI."
    )

ssl_options = None
if REDIS_URL.startswith("rediss://"):
    ssl_options = {
        "ssl_cert_reqs": ssl.CERT_NONE
    }

celery_app = Celery(
    "saar_ai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

if ssl_options:
    celery_app.conf.broker_use_ssl = ssl_options
    celery_app.conf.redis_backend_use_ssl = ssl_options