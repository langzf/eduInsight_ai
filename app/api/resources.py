from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import aiofiles
import os

from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from app.models.resource import Resource
from app.utils.storage import StorageService
from app.utils.content_check import ContentChecker

router = APIRouter()
storage = StorageService()
content_checker = ContentChecker()

@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    skip: int = 0,
    limit: int = 10,
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取资源列表"""
    query = db.query(Resource)
    
    if type:
        query = query.filter(Resource.type == type)
    if status:
        query = query.filter(Resource.status == status)
        
    total = query.count()
    resources = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": resources
    }

@router.post("/resources/chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """处理分片上传"""
    chunk_dir = os.path.join(settings.UPLOAD_DIR, file_id)
    os.makedirs(chunk_dir, exist_ok=True)
    
    chunk_path = os.path.join(chunk_dir, f"chunk_{chunk_index}")
    async with aiofiles.open(chunk_path, 'wb') as f:
        content = await chunk.read()
        await f.write(content)
    
    # 检查是否所有分片都已上传
    uploaded_chunks = len(os.listdir(chunk_dir))
    if uploaded_chunks == total_chunks:
        # 合并分片
        return await merge_chunks(file_id, db, current_user)
        
    return {"message": "Chunk uploaded successfully"}

@router.post("/resources/merge")
async def merge_chunks(
    file_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """合并分片"""
    chunk_dir = os.path.join(settings.UPLOAD_DIR, file_id)
    output_path = os.path.join(settings.UPLOAD_DIR, file_id + "_complete")
    
    # 合并所有分片
    async with aiofiles.open(output_path, 'wb') as outfile:
        chunks = sorted(os.listdir(chunk_dir), key=lambda x: int(x.split('_')[1]))
        for chunk in chunks:
            chunk_path = os.path.join(chunk_dir, chunk)
            async with aiofiles.open(chunk_path, 'rb') as infile:
                content = await infile.read()
                await outfile.write(content)
    
    # 上传到存储服务
    file_url = await storage.upload(output_path)
    
    # 创建资源记录
    resource = Resource(
        name=file_id,
        type=get_file_type(output_path),
        url=file_url,
        uploader_id=current_user.id,
        file_size=os.path.getsize(output_path),
        mime_type=get_mime_type(output_path)
    )
    db.add(resource)
    db.commit()
    
    # 清理临时文件
    os.remove(output_path)
    os.rmdir(chunk_dir)
    
    return {"id": resource.id, "url": file_url}

@router.post("/resources/{id}/review")
async def review_resource(
    id: int,
    status: str,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """审核资源"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No permission")
        
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    resource.status = status
    resource.reviewer_id = current_user.id
    resource.review_time = datetime.utcnow()
    resource.review_comment = comment
    
    db.commit()
    return {"message": "Review completed"}

@router.post("/resources/{id}/auto-review")
async def auto_review_resource(
    id: int,
    db: Session = Depends(get_db)
):
    """自动审核资源"""
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # 内容检查
    check_result = await content_checker.check(resource.url)
    
    # 更新审核结果
    resource.metadata["auto_review"] = {
        "sensitive_words": check_result.sensitive_words,
        "similarity_score": check_result.similarity,
        "quality_score": check_result.quality,
        "recommendation": check_result.recommendation
    }
    
    db.commit()
    return check_result

@router.get("/resources/{id}/presigned-url")
async def get_presigned_url(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取预签名URL"""
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    if resource.status != 'approved':
        raise HTTPException(status_code=403, detail="Resource not approved")
    
    url = await storage.get_presigned_url(resource.url)
    
    # 更新访问统计
    resource.view_count += 1
    db.commit()
    
    return {"url": url} 