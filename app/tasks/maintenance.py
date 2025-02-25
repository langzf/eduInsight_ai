from app import create_app
from app.celery_app import create_celery
import logging
from datetime import datetime
import os

app = create_app()
celery = create_celery(app)

@celery.task(name='app.tasks.maintenance.daily_backup')
def daily_backup():
    """每日备份任务"""
    try:
        # 创建备份目录
        backup_dir = os.path.join(
            app.config['BACKUP_DIR'],
            datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        os.makedirs(backup_dir, exist_ok=True)
        
        # 导出数据库
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        db_backup_path = os.path.join(backup_dir, 'database.sql')
        os.system(f'pg_dump {db_url} > {db_backup_path}')
        
        # 备份上传文件
        upload_dir = app.config['UPLOAD_FOLDER']
        files_backup_path = os.path.join(backup_dir, 'files')
        os.system(f'cp -r {upload_dir} {files_backup_path}')
        
        # 清理旧备份（保留最近7天）
        cleanup_old_backups(days=7)
        
        return {
            'success': True,
            'backup_path': backup_dir
        }
    except Exception as e:
        logging.error(f"每日备份失败: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery.task(name='app.tasks.maintenance.cleanup_old_backups')
def cleanup_old_backups(days: int = 7):
    """清理旧备份"""
    try:
        from datetime import datetime, timedelta
        backup_dir = app.config['BACKUP_DIR']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                try:
                    # 解析目录名中的日期
                    dir_date = datetime.strptime(item, '%Y%m%d_%H%M%S')
                    if dir_date < cutoff_date:
                        os.system(f'rm -rf {item_path}')
                except ValueError:
                    continue
                    
        return {'success': True}
    except Exception as e:
        logging.error(f"清理旧备份失败: {str(e)}")
        return {'success': False, 'error': str(e)} 