from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum('video', 'document', 'image', name='resource_type'), nullable=False)
    url = Column(String(1024), nullable=False)
    status = Column(Enum('pending', 'approved', 'rejected', name='review_status'), default='pending')
    
    file_size = Column(Integer)  # 文件大小(bytes)
    mime_type = Column(String(128))  # MIME类型
    metadata = Column(JSON)  # 元数据(如视频时长、文档页数等)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 上传者信息
    uploader_id = Column(Integer, ForeignKey("users.id"))
    uploader = relationship("User", back_populates="resources")
    
    # 审核信息
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_time = Column(DateTime, nullable=True)
    review_comment = Column(String(512), nullable=True)

    # 使用统计
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'url': self.url,
            'status': self.status,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'uploader_id': self.uploader_id,
            'reviewer_id': self.reviewer_id,
            'review_time': self.review_time,
            'review_comment': self.review_comment,
            'view_count': self.view_count,
            'download_count': self.download_count
        } 