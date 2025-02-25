from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

# 配置
SECRET_KEY = "your-secret-key"  # 应从环境变量获取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "admin": "管理员权限",
        "trainer": "模型训练权限",
        "predictor": "模型预测权限",
        "viewer": "只读权限"
    }
)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: List[str] = []

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    :param data: 令牌数据
    :param expires_delta: 过期时间
    :return: JWT令牌
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
        
    except Exception as e:
        logging.error(f"创建访问令牌失败: {str(e)}")
        raise

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户
    :param security_scopes: 安全作用域
    :param token: JWT令牌
    :return: 用户信息
    """
    try:
        # 验证令牌
        credentials_exception = HTTPException(
            status_code=401,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_scopes = payload.get("scopes", [])
            token_data = TokenData(username=username, scopes=token_scopes)
        except JWTError:
            raise credentials_exception
        
        # 获取用户信息
        user = get_user(username)
        if user is None:
            raise credentials_exception
        
        # 验证作用域
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=403,
                    detail="权限不足",
                    headers={"WWW-Authenticate": f"Bearer scope={scope}"},
                )
        
        return user
        
    except Exception as e:
        logging.error(f"获取当前用户失败: {str(e)}")
        raise

def get_user(username: str) -> Optional[User]:
    """
    获取用户信息
    :param username: 用户名
    :return: 用户信息
    """
    # 这里应该从数据库获取用户信息
    # 示例实现
    fake_users_db = {
        "admin": {
            "username": "admin",
            "full_name": "Administrator",
            "email": "admin@example.com",
            "hashed_password": get_password_hash("admin123"),
            "disabled": False,
            "roles": ["admin", "trainer", "predictor", "viewer"]
        },
        "trainer": {
            "username": "trainer",
            "full_name": "Model Trainer",
            "email": "trainer@example.com",
            "hashed_password": get_password_hash("trainer123"),
            "disabled": False,
            "roles": ["trainer", "predictor", "viewer"]
        }
    }
    
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return User(**user_dict)
    return None

def check_permissions(required_roles: List[str], user: User = Depends(get_current_user)) -> bool:
    """
    检查用户权限
    :param required_roles: 所需角色
    :param user: 用户信息
    :return: 是否有权限
    """
    try:
        return any(role in user.roles for role in required_roles)
    except Exception as e:
        logging.error(f"检查用户权限失败: {str(e)}")
        raise 