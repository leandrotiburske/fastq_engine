import os
import threading
from datetime import datetime
from dotenv import load_dotenv
import subprocess

from celery import Celery
from infra.main import SessionLocal
from crud.main import get_task

load_dotenv()

celery_app = Celery(
    'fastq_engine',
    broker=f"pyamqp://{os.getenv('USERNAME')}:{os.getenv('PASSWORD')}@rabbitmq:5672//",
)

@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def test_nextflow(self, task_id: int):
    """
    Run a test Nextflow pipeline (nf-core/sarek) and report progress.
    """
    db = SessionLocal()

    task = get_task(db, task_id)

    # Update DB with status and task id
    task.status = "RUNNING"
    task.celery_task_id = self.request.id
    task.started_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    db.commit()

    try:

        outdir = f"./test/{task.id}/"
        process = subprocess.Popen(
            ["nextflow", "run", "nf-core/sarek", 
             "-profile", "conda,test", 
             "--outdir", outdir, "-resume"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
            )
        
        task.outdir = outdir
        task.workdir = './work'
        task.updated_at = datetime.utcnow()
        db.commit()

        stdout_lines = []
        stderr_lines = []

        def read_stderr():
            for line in process.stderr:
                stderr_lines.append(line)

        stderr_thread = threading.Thread(target=read_stderr)
        stderr_thread.start()

        for line in process.stdout:
            stdout_lines.append(line)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': len(stdout_lines),
                    'status': line.strip()
                }
            )

        stderr_thread.join()

        process.wait()

        task.status = 'SUCCESS' if process.returncode == 0 else 'FAILURE'
        task.return_code = process.returncode
        task.updated_at = datetime.utcnow()
        task.completed_at = datetime.utcnow()
        db.commit()

        return {
            "return_code": process.returncode,
            "stdout": "".join(stdout_lines),
            "stderr": "".join(stderr_lines),
        }
    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        db.close()
