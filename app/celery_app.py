from celery import Celery
from flask import current_app
import os

def create_celery(app):
    """创建Celery实例"""
    # 检查环境变量，确定是否使用Redis
    use_redis = os.environ.get('USE_REDIS', 'false').lower() == 'true'
    
    # 如果不使用Redis，则使用内存作为中间件
    if not use_redis:
        broker_url = 'memory://'
        result_backend = 'db+sqlite:///celery-results.sqlite'
    else:
        broker_url = app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        result_backend = app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    celery = Celery(
        app.import_name,
        backend=result_backend,
        broker=broker_url
    )
    
    # 配置Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery 