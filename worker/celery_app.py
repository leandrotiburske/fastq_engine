import os
import threading
from dotenv import load_dotenv
import subprocess

from celery import Celery

load_dotenv()

celery_app = Celery(
    'fastq_engine',
    broker=f"pyamqp://{os.getenv('USERNAME')}:{os.getenv('PASSWORD')}@rabbitmq:5672//",
)

@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def test_nextflow(self):
    task_id = self.request.id
    outdir = f"./test/{task_id}/"
    process = subprocess.Popen(
        ["nextflow", "run", "nf-core/sarek", 
         "-profile", "conda,test", 
         "--outdir", outdir, "-resume"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
        )

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
    
    return {
        "rc": process.returncode,
        "stdout": "".join(stdout_lines),
        "stderr": "".join(stderr_lines),
    }
