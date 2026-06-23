import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from infra.main import get_db, Base, engine
from crud.main import create_task, get_all_tasks, get_task, get_tasks_by_patient
from worker.celery_app import submit_nextflow

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"message": "OK"}

@app.post("/submit_task")
async def submit_task(
    patient_name: str,
    patient_id: int,
    sex: str,
    fastq1: str,
    fastq2: str,
    session=Depends(get_db),
):
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        outdir = os.path.abspath(f"/app/samplesheets/{timestamp}")
        os.makedirs(outdir, exist_ok=True)

        samplesheet_path = os.path.join(outdir, f"samplesheet_{timestamp}.csv")

        with open(samplesheet_path, "w") as f:
            f.write("patient,sex,status,sample,lane,fastq_1,fastq_2\n")
            f.write(f"{patient_name},{sex},0,{patient_name},L1,{fastq1},{fastq2}\n")

        print("Samplesheet created:", samplesheet_path)

        task = create_task(session, patient_id)
        print("Task created:", task.id)

        submit_nextflow.delay(task.id, samplesheet_path, patient_name, patient_id)
        print("Celery dispatched")

        return {
            "id": task.id,
            "patient_id": task.patient_id,
            "status": task.status,
            "samplesheet_path": samplesheet_path,
        }

    except Exception as e:
        print(f"Error occurred in /submit_task: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_all_tasks")
async def get_tasks(session = Depends(get_db)):
    return get_all_tasks(session)

@app.get("/get_task/{task_id}")
async def get_single_task(task_id: int, session = Depends(get_db)):
    return get_task(session, task_id)

@app.get("/get_patient_tasks/{patient_id}")
async def get_patient_tasks(patient_id: int, session = Depends(get_db)):
    return get_tasks_by_patient(session, patient_id)
