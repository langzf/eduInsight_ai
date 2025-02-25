from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Security
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
from ..auth.security import get_current_user, User, Token, check_permissions
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer, SecurityScopes
from ..monitoring.metrics import track_metrics, MetricsCollector
from ..utils.cache import CacheManager, CACHE_KEYS

# 创建路由器
router = APIRouter(
    prefix="/model",
    tags=["model"],
    responses={
        401: {"description": "认证失败"},
        403: {"description": "权限不足"},
        500: {"description": "服务器内部错误"}
    }
)

# 请求/响应模型
class TrainingRequest(BaseModel):
    user_id: int
    model_type: str
    training_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None

class PredictionRequest(BaseModel):
    user_id: int
    model_type: str
    input_data: Dict[str, Any]

class CompressionRequest(BaseModel):
    user_id: int
    model_type: str
    compression_type: str
    compression_config: Optional[Dict[str, Any]] = None
    training_data: Optional[Dict[str, Any]] = None

class EnsembleRequest(BaseModel):
    user_id: int
    model_type: str
    model_ids: List[str]
    weights: Optional[List[float]] = None

class ApiResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 初始化缓存管理器
cache_manager = CacheManager(get_config())

# 训练相关路由
@router.post(
    "/train",
    response_model=ApiResponse,
    tags=["training"],
    summary="启动模型训练",
    description="""
    启动模型训练任务。
    
    支持:
    - 学生模型训练
    - 教师模型训练
    - 分布式训练
    
    请求参数:
    - user_id: 用户ID
    - model_type: 模型类型 ('student' 或 'teacher')
    - training_data: 训练数据
    - config: 训练配置(可选)
    
    权限要求:
    - trainer 或 admin 角色
    """
)
@track_metrics("/model/train")
async def train_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Security(
        get_current_user,
        scopes=["trainer", "admin"]
    )
) -> Dict[str, Any]:
    """
    启动模型训练
    """
    try:
        # 检查权限
        if not check_permissions(["trainer", "admin"], current_user):
            raise HTTPException(
                status_code=403,
                detail="没有训练权限"
            )
        
        # 验证请求
        if request.model_type not in ['student', 'teacher']:
            raise ValueError("不支持的模型类型")
        
        # 创建训练任务
        training_manager = get_training_manager()
        
        # 异步执行训练
        background_tasks.add_task(
            training_manager.train_distributed if request.config.get('distributed', False)
            else (
                training_manager.train_student_model
                if request.model_type == 'student'
                else training_manager.train_teacher_model
            ),
            get_model_instance(request.model_type, request.config),
            request.user_id,
            request.training_data
        )
        
        return {
            "status": "success",
            "message": "训练任务已启动",
            "data": {
                "user_id": request.user_id,
                "model_type": request.model_type,
                "task_id": str(datetime.now().timestamp())
            }
        }
        
    except Exception as e:
        logging.error(f"启动训练失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/status/{user_id}", response_model=ApiResponse)
@cache_manager.cache(
    CACHE_KEYS['training_status'],
    expire=60  # 1分钟缓存
)
async def get_training_status(user_id: int) -> Dict[str, Any]:
    """
    获取训练状态
    """
    try:
        training_manager = get_training_manager()
        status = training_manager.get_training_status(user_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="未找到训练状态")
        
        return {
            "status": "success",
            "message": "获取训练状态成功",
            "data": status
        }
        
    except Exception as e:
        logging.error(f"获取训练状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 预测相关路由
@router.post(
    "/predict",
    response_model=ApiResponse,
    tags=["prediction"],
    summary="模型预测",
    description="""
    使用训练好的模型进行预测。
    
    支持:
    - 学生模型预测
    - 教师模型预测
    - 集成模型预测
    
    请求参数:
    - user_id: 用户ID
    - model_type: 模型类型
    - input_data: 输入数据
    
    权限要求:
    - predictor, trainer 或 admin 角色
    """
)
@track_metrics("/model/predict")
@cache_manager.cache(
    CACHE_KEYS['prediction'],
    expire=300,  # 5分钟缓存
    condition=lambda request, **_: not request.config.get('no_cache', False)
)
async def predict(
    request: PredictionRequest,
    current_user: User = Security(
        get_current_user,
        scopes=["predictor", "trainer", "admin"]
    )
) -> Dict[str, Any]:
    """
    模型预测
    """
    try:
        # 检查权限
        if not check_permissions(["predictor", "trainer", "admin"], current_user):
            raise HTTPException(
                status_code=403,
                detail="没有预测权限"
            )
        
        training_manager = get_training_manager()
        
        # 执行预测
        predictions = training_manager.predict(
            request.input_data,
            request.user_id,
            request.model_type
        )
        
        return {
            "status": "success",
            "message": "预测成功",
            "data": predictions
        }
        
    except Exception as e:
        logging.error(f"预测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 模型压缩相关路由
@router.post("/compress", response_model=ApiResponse)
async def compress_model(
    request: CompressionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    压缩模型
    """
    try:
        # 检查权限
        if not check_permissions(["admin"], current_user):
            raise HTTPException(
                status_code=403,
                detail="没有模型压缩权限"
            )
        
        training_manager = get_training_manager()
        
        # 执行压缩
        result = training_manager.compress_model(
            get_model_instance(request.model_type),
            request.user_id,
            request.compression_type,
            request.compression_config,
            request.training_data
        )
        
        return {
            "status": "success",
            "message": "模型压缩成功",
            "data": result
        }
        
    except Exception as e:
        logging.error(f"模型压缩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 模型集成相关路由
@router.post("/ensemble", response_model=ApiResponse)
async def create_ensemble(
    request: EnsembleRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    创建模型集成
    """
    try:
        # 检查权限
        if not check_permissions(["admin"], current_user):
            raise HTTPException(
                status_code=403,
                detail="没有模型集成权限"
            )
        
        training_manager = get_training_manager()
        
        # 加载模型
        models = [
            load_model(model_id, request.model_type)
            for model_id in request.model_ids
        ]
        
        # 创建集成
        result = training_manager.create_model_ensemble(
            models,
            request.weights,
            request.user_id
        )
        
        return {
            "status": "success",
            "message": "模型集成创建成功",
            "data": result
        }
        
    except Exception as e:
        logging.error(f"创建模型集成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 可视化相关路由
@router.get("/visualize/{user_id}/{model_type}", response_model=ApiResponse)
@cache_manager.cache(
    CACHE_KEYS['visualization'],
    expire=3600  # 1小时缓存
)
async def get_visualizations(
    user_id: int,
    model_type: str,
    viz_type: str = 'training',
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取可视化结果
    """
    try:
        # 检查权限
        if not check_permissions(["viewer", "trainer", "admin"], current_user):
            raise HTTPException(
                status_code=403,
                detail="没有查看权限"
            )
        
        training_manager = get_training_manager()
        status = training_manager.get_training_status(user_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="未找到训练状态")
        
        visualizations = status.get('visualizations', {})
        
        return {
            "status": "success",
            "message": "获取可视化成功",
            "data": {
                "visualizations": visualizations,
                "type": viz_type
            }
        }
        
    except Exception as e:
        logging.error(f"获取可视化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
def get_training_manager():
    """获取训练管理器实例"""
    from model_service.utils.train_manager import TrainingManager
    from model_service.config import get_config
    
    config = get_config()
    return TrainingManager(config)

def get_model_instance(model_type: str, config: Optional[Dict[str, Any]] = None):
    """获取模型实例"""
    from model_service.models.student_model import StudentModel
    from model_service.models.teacher_model import TeacherModel
    from model_service.config import get_config
    
    model_config = config or get_config()
    
    if model_type == 'student':
        return StudentModel(model_config)
    elif model_type == 'teacher':
        return TeacherModel(model_config)
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")

def load_model(model_id: str, model_type: str):
    """加载模型"""
    from model_service.utils.model_manager import ModelManager
    from model_service.config import get_config
    
    config = get_config()
    manager = ModelManager(config)
    
    model_class = get_model_instance(model_type).__class__
    return manager.load_model(model_class, model_id)

# 认证路由
@router.post(
    "/token",
    response_model=Token,
    tags=["auth"],
    summary="获取访问令牌",
    description="""
    通过用户名和密码获取访问令牌。
    
    请求参数:
    - username: 用户名
    - password: 密码
    - scope: 请求的权限范围
    
    返回:
    - access_token: 访问令牌
    - token_type: 令牌类型
    """
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    获取访问令牌
    """
    try:
        user = get_user(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "scopes": form_data.scopes},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logging.error(f"获取访问令牌失败: {str(e)}")
        raise 