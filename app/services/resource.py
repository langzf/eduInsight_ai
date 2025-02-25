import boto3
from botocore.exceptions import ClientError
from flask import current_app
import logging
from typing import Optional, Dict, Any, List

class ResourceService:
    """资源服务类"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = current_app.config['AWS_S3_BUCKET']
    
    def upload_to_s3(self, file, folder: str) -> Optional[str]:
        """
        上传文件到S3
        :param file: 文件对象
        :param folder: 存储文件夹
        :return: 文件URL或None
        """
        try:
            file_name = f"{folder}/{file.filename}"
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                file_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file_name}"
        except ClientError as e:
            logging.error(f"S3上传失败: {str(e)}")
            return None
    
    def validate_resource(self, resource_data: Dict[str, Any]) -> bool:
        """
        验证资源数据
        :param resource_data: 资源数据
        :return: 是否有效
        """
        required_fields = ['title', 'type', 'tags']
        return all(field in resource_data for field in required_fields)
    
    def process_resource(self, file, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理资源上传
        :param file: 文件对象
        :param metadata: 资源元数据
        :return: 处理结果
        """
        if not self.validate_resource(metadata):
            return None
            
        file_url = self.upload_to_s3(file, metadata['type'])
        if not file_url:
            return None
            
        return {
            'url': file_url,
            'title': metadata['title'],
            'type': metadata['type'],
            'tags': metadata['tags'],
            'status': 'pending'
        }
    
    def get_recommended_resources(self, student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取推荐资源
        :param student_id: 学生ID
        :param limit: 返回数量限制
        :return: 推荐资源列表
        """
        try:
            from app.models.student import Student
            from app.models.resource import Resource
            
            student = Student.query.get(student_id)
            if not student or not student.weak_points:
                return []
            
            # 基于薄弱点匹配资源
            resources = Resource.query.filter(
                Resource.tags.contains(student.weak_points)
            ).order_by(Resource.rating.desc()).limit(limit).all()
            
            return [resource.to_dict() for resource in resources]
        except Exception as e:
            logging.error(f"获取推荐资源失败: {str(e)}")
            return []
    
    def analyze_resource_usage(self, resource_id: int) -> Dict[str, Any]:
        """
        分析资源使用情况
        :param resource_id: 资源ID
        :return: 使用统计
        """
        try:
            from app.models.resource import Resource
            from app.models.resource_usage import ResourceUsage
            
            resource = Resource.query.get(resource_id)
            if not resource:
                return {}
            
            usages = ResourceUsage.query.filter_by(resource_id=resource_id).all()
            
            return {
                'total_views': len(usages),
                'average_duration': sum(u.duration for u in usages) / len(usages) if usages else 0,
                'rating': resource.rating,
                'feedback_count': len([u for u in usages if u.feedback])
            }
        except Exception as e:
            logging.error(f"分析资源使用情况失败: {str(e)}")
            return {} 