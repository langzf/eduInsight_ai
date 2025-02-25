from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Dict, Any, Optional
import psutil
import logging
import time
from functools import wraps

# 创建指标注册表
REGISTRY = CollectorRegistry()

# API指标
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# 模型训练指标
model_training_status = Gauge(
    'model_training_status',
    'Model training status (0: idle, 1: training, 2: completed, 3: failed)',
    ['user_id', 'model_type'],
    registry=REGISTRY
)

model_training_progress = Gauge(
    'model_training_progress',
    'Model training progress percentage',
    ['user_id', 'model_type'],
    registry=REGISTRY
)

model_training_loss = Gauge(
    'model_training_loss',
    'Model training loss value',
    ['user_id', 'model_type'],
    registry=REGISTRY
)

# 系统资源指标
system_cpu_usage = Gauge(
    'system_cpu_usage',
    'System CPU usage percentage',
    registry=REGISTRY
)

system_memory_usage = Gauge(
    'system_memory_usage',
    'System memory usage percentage',
    registry=REGISTRY
)

gpu_memory_usage = Gauge(
    'gpu_memory_usage',
    'GPU memory usage percentage',
    ['device_id'],
    registry=REGISTRY
)

class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def track_request_metrics(method: str, endpoint: str, status: int, duration: float):
        """
        跟踪请求指标
        :param method: HTTP方法
        :param endpoint: 端点
        :param status: 状态码
        :param duration: 持续时间
        """
        try:
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
        except Exception as e:
            logging.error(f"跟踪请求指标失败: {str(e)}")
    
    @staticmethod
    def update_training_metrics(
        user_id: int,
        model_type: str,
        status: int,
        progress: float,
        loss: Optional[float] = None
    ):
        """
        更新训练指标
        :param user_id: 用户ID
        :param model_type: 模型类型
        :param status: 训练状态
        :param progress: 训练进度
        :param loss: 损失值
        """
        try:
            model_training_status.labels(
                user_id=str(user_id),
                model_type=model_type
            ).set(status)
            
            model_training_progress.labels(
                user_id=str(user_id),
                model_type=model_type
            ).set(progress)
            
            if loss is not None:
                model_training_loss.labels(
                    user_id=str(user_id),
                    model_type=model_type
                ).set(loss)
                
        except Exception as e:
            logging.error(f"更新训练指标失败: {str(e)}")
    
    @staticmethod
    def collect_system_metrics():
        """收集系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent()
            system_cpu_usage.set(cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.percent)
            
            # GPU使用率(如果可用)
            try:
                import torch
                if torch.cuda.is_available():
                    for i in range(torch.cuda.device_count()):
                        memory_stats = torch.cuda.memory_stats(i)
                        memory_used = memory_stats["allocated_bytes.all.current"]
                        memory_total = torch.cuda.get_device_properties(i).total_memory
                        gpu_memory_usage.labels(device_id=str(i)).set(
                            memory_used / memory_total * 100
                        )
            except ImportError:
                pass
                
        except Exception as e:
            logging.error(f"收集系统指标失败: {str(e)}")

def track_metrics(endpoint: str):
    """
    请求指标跟踪装饰器
    :param endpoint: API端点
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = response.status_code if hasattr(response, 'status_code') else 200
                return response
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                MetricsCollector.track_request_metrics(
                    method=kwargs.get('request', args[0]).method,
                    endpoint=endpoint,
                    status=status,
                    duration=duration
                )
        return wrapper
    return decorator 