from typing import Optional
import boto3
import oss2
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER
        if self.provider == 's3':
            self.client = boto3.client('s3',
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
                region_name=settings.AWS_REGION
            )
        elif self.provider == 'oss':
            self.auth = oss2.Auth(
                settings.OSS_ACCESS_KEY,
                settings.OSS_SECRET_KEY
            )
            self.bucket = oss2.Bucket(
                self.auth,
                settings.OSS_ENDPOINT,
                settings.OSS_BUCKET
            )
    
    async def upload(self, file_path: str) -> str:
        """上传文件到存储服务"""
        key = generate_storage_key(file_path)
        
        if self.provider == 's3':
            self.client.upload_file(file_path, settings.AWS_BUCKET, key)
            return f"https://{settings.AWS_BUCKET}.s3.amazonaws.com/{key}"
            
        elif self.provider == 'oss':
            self.bucket.put_object_from_file(key, file_path)
            return f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}/{key}"
            
        return f"/storage/{key}"  # 本地存储
        
    async def get_presigned_url(self, url: str, expires: int = 3600) -> str:
        """获取预签名URL"""
        key = extract_key_from_url(url)
        
        if self.provider == 's3':
            return self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_BUCKET, 'Key': key},
                ExpiresIn=expires
            )
            
        elif self.provider == 'oss':
            return self.bucket.sign_url('GET', key, expires)
            
        return url  # 本地存储直接返回原URL 