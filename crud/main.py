from fastapi import HTTPException
from models.main import Tasks
from infra.main import SessionLocal

def create_task(db_session, patient_id: int):
    """
    Create new task

    :param db_session: DB session
    """
    try:
        task = Tasks(
            status='PENDING',
            patient_id=patient_id,
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_all_tasks(db_session):
    """
    Retrieves all available tasks in the DB

    :param db_session: DB session
    """
    try:
        all_tasks = db_session.query(Tasks).all()
        return all_tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_task(db_session, task_id: int):
    """
    Retrieve a single task from the DB by ID
    
    :param db_session: DB session
    :param task_id: ID of task
    :type task_id: int
    """
    try:
        task = db_session.query(Tasks).filter(Tasks.id == task_id).first()
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_tasks_by_patient(db_session, patient_id: int):
    """
    Retrieve all tasks for a single patient by patient ID
        
    :param db_session: DB session
    :param patient_id: Patient ID
    :type patient_id: int
    """
    try:
        tasks = db_session.query(Tasks).filter(Tasks.patient_id == patient_id).all()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
