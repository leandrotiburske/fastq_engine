from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from infra.main import get_db, Base, engine
from crud.main import create_task, get_all_tasks, get_task, get_tasks_by_patient
from worker.celery_app import test_nextflow

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
    patient_id: int,
    session = Depends(get_db),
):
    task = create_task(session, patient_id)
    test_nextflow.delay(task.id)

    return task
    
@app.get("/get_all_tasks")
async def get_tasks(session = Depends(get_db)):
    return get_all_tasks(session)

@app.get("/get_task/{task_id}")
async def get_single_task(task_id: int, session = Depends(get_db)):
    return get_task(session, task_id)

@app.get("/get_patient_tasks/{patient_id}")
async def get_patient_tasks(patient_id: int, session = Depends(get_db)):
    return get_tasks_by_patient(session, patient_id)
