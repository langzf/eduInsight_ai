import pytest
import asyncio
from typing import Dict, Any
import requests
import json
import time
from pathlib import Path

# 测试配置
API_BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = Path("test_e2e_data")

class TestEndToEnd:
    """端到端测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试环境设置"""
        TEST_DATA_DIR.mkdir(exist_ok=True)
        
        # 获取认证令牌
        response = requests.post(
            f"{API_BASE_URL}/model/token",
            data={
                "username": "admin",
                "password": "admin123",
                "scope": "admin trainer predictor viewer"
            }
        )
        self.auth_token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        yield
        
        # 清理测试数据
        import shutil
        shutil.rmtree(TEST_DATA_DIR)
    
    def test_complete_model_lifecycle(self):
        """测试完整模型生命周期"""
        # 1. 训练模型
        training_data = {
            "user_id": 1,
            "model_type": "student",
            "training_data": {
                "text": ["内容1", "内容2"],
                "sequence": [[1, 2, 3], [4, 5, 6]],
                "labels": {
                    "weaknesses": [[1, 0], [0, 1]],
                    "interests": [[0, 1], [1, 0]],
                    "path": [[0.7, 0.3], [0.4, 0.6]]
                }
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/model/train",
            headers=self.headers,
            json=training_data
        )
        assert response.status_code == 200
        task_id = response.json()['data']['task_id']
        
        # 2. 等待训练完成
        max_wait = 300  # 5分钟
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{API_BASE_URL}/model/training/status/1",
                headers=self.headers
            )
            if response.status_code == 200:
                status = response.json()['data']['status']
                if status == 'completed':
                    break
            time.sleep(5)
        
        assert status == 'completed'
        
        # 3. 压缩模型
        compression_request = {
            "user_id": 1,
            "model_type": "student",
            "compression_type": "pruning",
            "compression_config": {
                "method": "l1_unstructured",
                "amount": 0.3
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/model/compress",
            headers=self.headers,
            json=compression_request
        )
        assert response.status_code == 200
        
        # 4. 执行预测
        prediction_request = {
            "user_id": 1,
            "model_type": "student",
            "input_data": {
                "text": "测试内容",
                "sequence": [1, 2, 3]
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/model/predict",
            headers=self.headers,
            json=prediction_request
        )
        assert response.status_code == 200
        predictions = response.json()['data']['predictions']
        
        # 5. 获取可视化
        response = requests.get(
            f"{API_BASE_URL}/model/visualize/1/student",
            headers=self.headers
        )
        assert response.status_code == 200
        assert 'visualizations' in response.json()['data']
    
    def test_error_handling_scenarios(self):
        """测试错误处理场景"""
        # 1. 无效认证
        response = requests.post(
            f"{API_BASE_URL}/model/predict",
            headers={"Authorization": "Bearer invalid_token"},
            json={}
        )
        assert response.status_code == 401
        
        # 2. 无效请求格式
        response = requests.post(
            f"{API_BASE_URL}/model/train",
            headers=self.headers,
            json={}
        )
        assert response.status_code == 422
        
        # 3. 资源不存在
        response = requests.get(
            f"{API_BASE_URL}/model/training/status/999",
            headers=self.headers
        )
        assert response.status_code == 404
    
    def test_concurrent_operations(self):
        """测试并发操作"""
        # 1. 并发训练请求
        training_requests = []
        for i in range(3):
            training_requests.append({
                "user_id": i + 1,
                "model_type": "student",
                "training_data": {
                    "text": [f"内容{j}" for j in range(5)],
                    "sequence": [[j, j+1, j+2] for j in range(5)],
                    "labels": {
                        "weaknesses": [[1, 0] for _ in range(5)],
                        "interests": [[0, 1] for _ in range(5)],
                        "path": [[0.7, 0.3] for _ in range(5)]
                    }
                }
            })
        
        # 发送并发请求
        async def send_requests():
            tasks = []
            for req in training_requests:
                tasks.append(
                    asyncio.create_task(
                        asyncio.to_thread(
                            requests.post,
                            f"{API_BASE_URL}/model/train",
                            headers=self.headers,
                            json=req
                        )
                    )
                )
            responses = await asyncio.gather(*tasks)
            return responses
        
        responses = asyncio.run(send_requests())
        assert all(r.status_code == 200 for r in responses) 