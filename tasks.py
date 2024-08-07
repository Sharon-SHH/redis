from celery import shared_task

@shared_task
def add_together(a: int, b: int) -> int:
    return a + b