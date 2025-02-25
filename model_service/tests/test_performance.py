import pytest
import asyncio
import time
import psutil
import numpy as np
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import logging
from statistics import mean, stdev
import json
from datetime import datetime

from model_service.main import app
from model_service.utils.train_manager import TrainingManager

# 测试客户端
client = TestClient(app)

# 性能指标记录器
class PerformanceMetrics:
    """性能指标记录"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count: int = 0
        self.success_count: int = 0
        self.start_time: float = time.time()
        self.end_time: float = 0
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []
    
    def add_response_time(self, response_time: float):
        """添加响应时间"""
        self.response_times.append(response_time)
    
    def add_error(self):
        """添加错误计数"""
        self.error_count += 1
    
    def add_success(self):
        """添加成功计数"""
        self.success_count += 1
    
    def record_system_metrics(self):
        """记录系统指标"""
        self.cpu_usage.append(psutil.cpu_percent())
        self.memory_usage.append(psutil.virtual_memory().percent)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if not self.response_times:
            return {
                "error": "No response times recorded"
            }
        
        return {
            "total_requests": len(self.response_times),
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "total_duration": duration,
            "requests_per_second": len(self.response_times) / duration,
            "response_time": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": mean(self.response_times),
                "p50": np.percentile(self.response_times, 50),
                "p90": np.percentile(self.response_times, 90),
                "p95": np.percentile(self.response_times, 95),
                "p99": np.percentile(self.response_times, 99),
                "std": stdev(self.response_times) if len(self.response_times) > 1 else 0
            },
            "system_metrics": {
                "cpu_usage": {
                    "mean": mean(self.cpu_usage),
                    "max": max(self.cpu_usage)
                },
                "memory_usage": {
                    "mean": mean(self.memory_usage),
                    "max": max(self.memory_usage)
                }
            }
        }
    
    def save_report(self, test_name: str):
        """保存性能报告"""
        try:
            report = {
                "test_name": test_name,
                "timestamp": datetime.now().isoformat(),
                "metrics": self.get_summary()
            }
            
            filename = f"performance_report_{test_name}_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存性能报告失败: {str(e)}")

# 测试数据
@pytest.fixture
def auth_token() -> str:
    """获取认证令牌"""
    response = client.post(
        "/model/token",
        data={
            "username": "admin",
            "password": "admin123",
            "scope": "admin trainer predictor viewer"
        }
    )
    return response.json()["access_token"]

@pytest.fixture
def prediction_request() -> Dict[str, Any]:
    """预测请求数据"""
    return {
        "user_id": 1,
        "model_type": "student",
        "input_data": {
            "text": "学习内容",
            "sequence": [1, 2, 3]
        }
    }

# 性能测试
class TestAPIPerformance:
    """API性能测试"""
    
    def make_request(self,
                    endpoint: str,
                    method: str = 'GET',
                    data: Dict[str, Any] = None,
                    headers: Dict[str, str] = None) -> float:
        """
        发送请求并计时
        :return: 响应时间(秒)
        """
        start_time = time.time()
        try:
            if method == 'GET':
                response = client.get(endpoint, headers=headers)
            else:
                response = client.post(endpoint, headers=headers, json=data)
            
            duration = time.time() - start_time
            return duration, response.status_code == 200
            
        except Exception as e:
            logging.error(f"请求失败: {str(e)}")
            return time.time() - start_time, False
    
    def test_prediction_latency(self,
                              auth_token: str,
                              prediction_request: Dict[str, Any]):
        """测试预测延迟"""
        metrics = PerformanceMetrics()
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 预热
        for _ in range(5):
            self.make_request(
                "/model/predict",
                method='POST',
                data=prediction_request,
                headers=headers
            )
        
        # 测试延迟
        n_requests = 100
        for _ in range(n_requests):
            duration, success = self.make_request(
                "/model/predict",
                method='POST',
                data=prediction_request,
                headers=headers
            )
            metrics.add_response_time(duration)
            if success:
                metrics.add_success()
            else:
                metrics.add_error()
            metrics.record_system_metrics()
        
        # 保存报告
        metrics.save_report("prediction_latency")
        summary = metrics.get_summary()
        
        # 验证性能指标
        assert summary["response_time"]["p95"] < 0.5  # 95%请求在500ms内完成
        assert summary["response_time"]["mean"] < 0.2  # 平均响应时间小于200ms
        assert summary["failed_requests"] == 0  # 无失败请求
    
    def test_concurrent_predictions(self,
                                 auth_token: str,
                                 prediction_request: Dict[str, Any]):
        """测试并发预测"""
        metrics = PerformanceMetrics()
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        async def make_concurrent_requests(n_requests: int):
            tasks = []
            for _ in range(n_requests):
                tasks.append(
                    asyncio.create_task(
                        asyncio.to_thread(
                            self.make_request,
                            "/model/predict",
                            'POST',
                            prediction_request,
                            headers
                        )
                    )
                )
            results = await asyncio.gather(*tasks)
            return results
        
        # 执行并发测试
        n_concurrent = 50
        results = asyncio.run(make_concurrent_requests(n_concurrent))
        
        # 记录结果
        for duration, success in results:
            metrics.add_response_time(duration)
            if success:
                metrics.add_success()
            else:
                metrics.add_error()
            metrics.record_system_metrics()
        
        # 保存报告
        metrics.save_report("concurrent_predictions")
        summary = metrics.get_summary()
        
        # 验证性能指标
        assert summary["requests_per_second"] > 10  # 每秒处理10个以上请求
        assert summary["response_time"]["p99"] < 2.0  # 99%请求在2秒内完成
        assert summary["system_metrics"]["cpu_usage"]["mean"] < 80  # CPU使用率小于80%
    
    def test_training_resource_usage(self,
                                   auth_token: str):
        """测试训练资源使用"""
        metrics = PerformanceMetrics()
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        training_request = {
            "user_id": 1,
            "model_type": "student",
            "training_data": {
                "text": ["内容" + str(i) for i in range(100)],
                "sequence": [[i, i+1, i+2] for i in range(100)],
                "labels": {
                    "weaknesses": [[1, 0] for _ in range(100)],
                    "interests": [[0, 1] for _ in range(100)],
                    "path": [[0.7, 0.3] for _ in range(100)]
                }
            }
        }
        
        # 启动训练
        start_time = time.time()
        response = client.post(
            "/model/train",
            headers=headers,
            json=training_request
        )
        assert response.status_code == 200
        task_id = response.json()['data']['task_id']
        
        # 监控资源使用
        max_wait_time = 300  # 最多等待5分钟
        while time.time() - start_time < max_wait_time:
            metrics.record_system_metrics()
            
            # 检查训练状态
            status_response = client.get(
                f"/model/training/status/1",
                headers=headers
            )
            if status_response.status_code == 200:
                status = status_response.json()['data']['status']
                if status in ['completed', 'failed']:
                    break
            
            time.sleep(5)  # 每5秒检查一次
        
        # 保存报告
        metrics.save_report("training_resource_usage")
        summary = metrics.get_summary()
        
        # 验证资源使用
        assert summary["system_metrics"]["memory_usage"]["max"] < 90  # 内存使用率小于90%
        assert summary["system_metrics"]["cpu_usage"]["mean"] < 85  # 平均CPU使用率小于85%
    
    def test_model_compression_performance(self,
                                        auth_token: str):
        """测试模型压缩性能"""
        metrics = PerformanceMetrics()
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        compression_request = {
            "user_id": 1,
            "model_type": "student",
            "compression_type": "pruning",
            "compression_config": {
                "method": "l1_unstructured",
                "amount": 0.3
            }
        }
        
        # 执行压缩
        start_time = time.time()
        response = client.post(
            "/model/compress",
            headers=headers,
            json=compression_request
        )
        duration = time.time() - start_time
        
        metrics.add_response_time(duration)
        metrics.record_system_metrics()
        
        # 保存报告
        metrics.save_report("model_compression")
        summary = metrics.get_summary()
        
        # 验证性能
        assert summary["response_time"]["mean"] < 30  # 压缩时间小于30秒
        assert summary["system_metrics"]["memory_usage"]["max"] < 85  # 内存使用率小于85%

def run_load_test(
    endpoint: str,
    n_requests: int,
    n_concurrent: int,
    request_data: Dict[str, Any],
    headers: Dict[str, str]
) -> PerformanceMetrics:
    """
    执行负载测试
    :param endpoint: API端点
    :param n_requests: 总请求数
    :param n_concurrent: 并发数
    :param request_data: 请求数据
    :param headers: 请求头
    :return: 性能指标
    """
    metrics = PerformanceMetrics()
    
    def worker():
        duration, success = TestAPIPerformance().make_request(
            endpoint,
            method='POST',
            data=request_data,
            headers=headers
        )
        metrics.add_response_time(duration)
        if success:
            metrics.add_success()
        else:
            metrics.add_error()
        metrics.record_system_metrics()
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=n_concurrent) as executor:
        futures = [executor.submit(worker) for _ in range(n_requests)]
        for future in futures:
            future.result()
    
    return metrics

if __name__ == '__main__':
    # 执行负载测试
    auth_token = client.post(
        "/model/token",
        data={
            "username": "admin",
            "password": "admin123",
            "scope": "admin"
        }
    ).json()["access_token"]
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    prediction_data = {
        "user_id": 1,
        "model_type": "student",
        "input_data": {
            "text": "测试内容",
            "sequence": [1, 2, 3]
        }
    }
    
    # 预测服务负载测试
    metrics = run_load_test(
        endpoint="/model/predict",
        n_requests=1000,
        n_concurrent=50,
        request_data=prediction_data,
        headers=headers
    )
    
    # 保存报告
    metrics.save_report("load_test_prediction")
    print(json.dumps(metrics.get_summary(), indent=2)) 