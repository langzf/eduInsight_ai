from typing import Dict, Any
from fastapi.openapi.utils import get_openapi

# API标签描述
tags_metadata = [
    {
        "name": "auth",
        "description": "认证相关接口，包括登录和令牌管理"
    },
    {
        "name": "training",
        "description": "模型训练相关接口，包括训练启动、状态查询等"
    },
    {
        "name": "prediction",
        "description": "模型预测相关接口"
    },
    {
        "name": "model",
        "description": "模型管理相关接口，包括压缩、集成等"
    },
    {
        "name": "visualization",
        "description": "可视化相关接口"
    }
]

# 示例请求/响应
examples = {
    "training_request": {
        "user_id": 1,
        "model_type": "student",
        "training_data": {
            "text": ["学习内容1", "学习内容2"],
            "sequence": [[1, 2, 3], [4, 5, 6]],
            "labels": {
                "weaknesses": [[1, 0, 1], [0, 1, 0]],
                "interests": [[0, 1, 0], [1, 0, 1]],
                "path": [[0.1, 0.2, 0.7], [0.3, 0.5, 0.2]]
            }
        },
        "config": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100
        }
    },
    "prediction_request": {
        "user_id": 1,
        "model_type": "student",
        "input_data": {
            "text": "学习内容",
            "sequence": [1, 2, 3]
        }
    }
}

def custom_openapi() -> Dict[str, Any]:
    """
    自定义OpenAPI文档
    :return: OpenAPI规范
    """
    from model_service.main import app
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Model Service API",
        version="1.0.0",
        description="""
        # AI教育模型服务API文档
        
        ## 功能特点
        - 模型训练和预测
        - 模型压缩和集成
        - 可视化支持
        - 完整的认证授权
        
        ## 使用说明
        1. 首先通过认证接口获取访问令牌
        2. 使用令牌访问其他接口
        3. 根据角色权限访问相应功能
        
        ## 注意事项
        - 所有请求需要携带有效的访问令牌
        - 部分接口需要特定的角色权限
        - 大规模训练任务建议使用异步接口
        """,
        routes=app.routes,
        tags=tags_metadata
    )
    
    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "token",
                    "scopes": {
                        "admin": "管理员权限",
                        "trainer": "模型训练权限",
                        "predictor": "模型预测权限",
                        "viewer": "只读权限"
                    }
                }
            }
        }
    }
    
    # 添加示例
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "requestBody" in method:
                method["requestBody"]["content"]["application/json"]["example"] = \
                    examples.get(method["operationId"])
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 