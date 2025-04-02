from flask_jwt_extended import jwt_required, get_jwt_identity
from fastapi import Depends, HTTPException, status
from typing import Optional

from app.models.user import User

def get_current_user():
    """
    获取当前登录用户
    """
    # JWT身份验证
    @jwt_required()
    def _get_current_user():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return None
        return user
    
    return _get_current_user()

# 基于FastAPI的依赖项函数
async def get_current_active_user(user = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证的用户",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user 