import os
from dotenv import load_dotenv
import subprocess

from celery import Celery

load_dotenv()

celery_app = Celery(
    'fastq_engine',
    broker=f"pyamqp://{os.getenv('USERNAME')}:{os.getenv('PASSWORD')}@rabbitmq:5672//",
)

@celery_app.task(bind=True)
def test_nextflow(self):
    result = subprocess.run(
        ["nextflow"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
        )

    return {
        "rc": result.returncode,
        "stdout": result.stdout[:500],
        "stderr": result.stderr[:500],
    }
