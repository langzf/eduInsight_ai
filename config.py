import os
from datetime import timedelta
from celery.schedules import crontab

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    
    # Celery配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/1'
    
    # 定时任务配置
    CELERY_BEAT_SCHEDULE = {
        'daily-student-notification': {
            'task': 'app.tasks.notifications.send_daily_notifications',
            'schedule': crontab(hour=8, minute=0)  # 每天早上8点
        },
        'weekly-analytics': {
            'task': 'app.tasks.analytics.generate_weekly_reports',
            'schedule': crontab(day_of_week=0, hour=0, minute=0)  # 每周日凌晨
        },
        'daily-backup': {
            'task': 'app.tasks.maintenance.daily_backup',
            'schedule': crontab(hour=2, minute=0)  # 每天凌晨2点
        }
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://username:password@localhost/eduinsight_dev'

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 