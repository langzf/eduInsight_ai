from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as model_router
from .api.docs import custom_openapi
import logging
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import asyncio
from .monitoring.metrics import MetricsCollector

# 创建应用
app = FastAPI(
    title="Model Service API",
    description="AI教育模型服务API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"  # OpenAPI规范
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(model_router)

# 自定义OpenAPI文档
app.openapi = custom_openapi

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加监控端点
@app.get("/metrics")
async def metrics():
    """导出Prometheus指标"""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# 系统指标收集任务
async def collect_system_metrics():
    """定期收集系统指标"""
    while True:
        MetricsCollector.collect_system_metrics()
        await asyncio.sleep(15)  # 每15秒收集一次

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logging.info("Model Service API 启动")
    
    # 启动系统指标收集
    asyncio.create_task(collect_system_metrics())

@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logging.info("Model Service API 关闭") 