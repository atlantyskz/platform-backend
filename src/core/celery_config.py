# celery_config.py
from celery import  Celery
def create_celery():
    celery_app = Celery(
        'app',
        broker='redis://redis:6379/0',
        backend='redis://redis:6379/0',
        include=['src.core.tasks']  # Include tasks modules
    )
    
    # Configure Celery
    celery_app.conf.update(
        enable_utc=True,
        accept_content=[ 'json'],
        task_serializer='json',
        result_serializer='json',
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True
    )
    
    return celery_app

# Initialize celery app
celery_app = create_celery()