from worker.celery_app import test_nextflow

result = test_nextflow.delay()
print(result.id) 
