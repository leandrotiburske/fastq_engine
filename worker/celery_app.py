import os
import gzip
import threading
import requests
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
def submit_nextflow(self, task_id: int, samplesheet_path: str, patient_name: str, patient_id: int):
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
        os.makedirs(outdir, exist_ok=True)
        stdout_log_path = os.path.join(outdir, "stdout.log")
        stderr_log_path = os.path.join(outdir, "stderr.log")

        process = subprocess.Popen(
            ["nextflow", "run", "nf-core/sarek", 
             "--input", samplesheet_path,
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

        with open(stdout_log_path, "w") as stdout_file, open(stderr_log_path, "w") as stderr_file:

            def read_stderr():
                for line in process.stderr:
                    stderr_lines.append(line)
                    stderr_file.write(line)
                    stderr_file.flush()

            stderr_thread = threading.Thread(target=read_stderr)
            stderr_thread.start()

            for line in process.stdout:
                stdout_lines.append(line)
                stdout_file.write(line)
                stdout_file.flush()

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": len(stdout_lines),
                        "status": line.strip()
                    }
                )

            stderr_thread.join()
            process.wait()

        task.status = 'SUCCESS' if process.returncode == 0 else 'FAILURE'
        task.return_code = process.returncode
        task.updated_at = datetime.utcnow()
        task.completed_at = datetime.utcnow()
        db.commit()

        if process.returncode == 0:
            vcf_file = outdir + "variant_calling/strelka/" + f"{patient_name}/{patient_name}.strelka.variants.vcf.gz"
            print(f"Looking for VCF file at: {vcf_file}")

            if os.path.exists(vcf_file):

                print(f"VCF file found: {vcf_file}")

                with gzip.open(vcf_file, 'rt') as f:
                    for line in f:
                        if line.startswith("#"):
                            continue
                        if line.startswith("#CHROM"):
                            continue

                        fields = line.strip().split("\t")

                        chrom = fields[0].replace("chr", "")    
                        if chrom == "M":
                            chrom = "MT"
                        pos = int(fields[1])
                        id = fields[2]
                        ref = fields[3]
                        alt = fields[4]

                        response = requests.post(
                            "http://host.docker.internal:8080/variants",
                            json={
                                "chromosome": chrom,
                                "position": pos,
                                "reference": ref,
                                "alternative": alt,
                                "gene": None,
                                "classification": None,
                                "phenotypes": None,
                                "external_id": id,
                                "publications": None,
                            },
                            timeout=120
                        )

                        print("POST status:", response.status_code)
                        print("POST response:", response.text)

                        response.raise_for_status()

                        created_variant = response.json()
                        variant_id = created_variant["id"]

                        response = requests.patch(
                            f"http://host.docker.internal:8080/subjects/{patient_id}/add_variants",
                            params={
                                "variant_id": variant_id
                            },
                            timeout=120
                        )

                        print("PATCH status:", response.status_code)
                        print("PATCH response:", response.text)

        return {
            "return_code": process.returncode,
            "stdout": "".join(stdout_lines),
            "stderr": "".join(stderr_lines),
        }
    except Exception as e:
        task.status = "FAILURE"
        task.updated_at = datetime.utcnow()
        task.completed_at = datetime.utcnow()
        db.commit()
        print(f"Error occurred: {e}")
        print(f"Error occurred: {e}")
        raise e

    finally:
        db.close()
