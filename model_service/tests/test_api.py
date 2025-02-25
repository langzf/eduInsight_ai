import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from model_service.main import app
from model_service.api.routes import get_training_manager
from model_service.utils.train_manager import TrainingManager

# 测试客户端
client = TestClient(app)

# 测试数据
@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """认证头"""
    # 获取访问令牌
    response = client.post(
        "/model/token",
        data={
            "username": "admin",
            "password": "admin123",
            "scope": "admin trainer predictor viewer"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def student_training_request() -> Dict[str, Any]:
    """学生模型训练请求"""
    return {
        "user_id": 1,
        "model_type": "student",
        "training_data": {
            "text": ["学习内容1", "学习内容2"],
            "sequence": [[1, 2, 3], [4, 5, 6]],
            "labels": {
                "weaknesses": [[1, 0], [0, 1]],
                "interests": [[0, 1], [1, 0]],
                "path": [[0.7, 0.3], [0.4, 0.6]]
            }
        },
        "config": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10
        }
    }

@pytest.fixture
def teacher_training_request() -> Dict[str, Any]:
    """教师模型训练请求"""
    return {
        "user_id": 1,
        "model_type": "teacher",
        "training_data": {
            "content": {
                "plans": ["教学计划1", "教学计划2"],
                "recordings": ["课堂记录1", "课堂记录2"],
                "feedback": ["反馈1", "反馈2"]
            },
            "student_data": [
                {
                    "average_score": 85,
                    "attendance_rate": 0.9,
                    "participation_rate": 0.8,
                    "homework_completion_rate": 0.95
                }
            ],
            "labels": {
                "coverage": {"math": 0.8, "physics": 0.7},
                "student_layers": [0.2, 0.5, 0.3]
            }
        }
    }

@pytest.fixture
def prediction_request() -> Dict[str, Any]:
    """预测请求"""
    return {
        "user_id": 1,
        "model_type": "student",
        "input_data": {
            "text": "学习内容",
            "sequence": [1, 2, 3]
        }
    }

# API测试
class TestModelAPI:
    """模型服务API测试"""
    
    def test_auth_token(self):
        """测试认证令牌"""
        response = client.post(
            "/model/token",
            data={
                "username": "admin",
                "password": "admin123",
                "scope": "admin"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
    
    def test_invalid_auth(self):
        """测试无效认证"""
        response = client.post(
            "/model/token",
            data={
                "username": "invalid",
                "password": "invalid",
                "scope": "admin"
            }
        )
        assert response.status_code == 401
    
    def test_train_student_model(self,
                               auth_headers: Dict[str, str],
                               student_training_request: Dict[str, Any]):
        """测试学生模型训练API"""
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            # 模拟训练管理器
            mock_manager = MagicMock()
            mock_manager.train_student_model.return_value = {
                'status': 'success',
                'model_path': '/path/to/model',
                'training_info': {'status': 'completed'}
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/model/train",
                headers=auth_headers,
                json=student_training_request
            )
            
            assert response.status_code == 200
            assert response.json()['status'] == 'success'
            assert 'task_id' in response.json()['data']
    
    def test_train_teacher_model(self,
                               auth_headers: Dict[str, str],
                               teacher_training_request: Dict[str, Any]):
        """测试教师模型训练API"""
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.train_teacher_model.return_value = {
                'status': 'success',
                'model_path': '/path/to/model',
                'training_info': {'status': 'completed'}
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/model/train",
                headers=auth_headers,
                json=teacher_training_request
            )
            
            assert response.status_code == 200
            assert response.json()['status'] == 'success'
    
    def test_get_training_status(self, auth_headers: Dict[str, str]):
        """测试获取训练状态API"""
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_training_status.return_value = {
                'status': 'completed',
                'progress': 100,
                'metrics': {'accuracy': 0.95}
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.get(
                "/model/training/status/1",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.json()['data']['status'] == 'completed'
    
    def test_model_prediction(self,
                            auth_headers: Dict[str, str],
                            prediction_request: Dict[str, Any]):
        """测试模型预测API"""
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.predict.return_value = {
                'predictions': {
                    'weaknesses': [{'label': 'concept', 'probability': 0.8}],
                    'interests': [{'label': 'theory', 'probability': 0.7}],
                    'learning_path': [{'step': 'basic', 'probability': 0.6}]
                }
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/model/predict",
                headers=auth_headers,
                json=prediction_request
            )
            
            assert response.status_code == 200
            assert 'predictions' in response.json()['data']
    
    def test_model_compression(self, auth_headers: Dict[str, str]):
        """测试模型压缩API"""
        compression_request = {
            "user_id": 1,
            "model_type": "student",
            "compression_type": "pruning",
            "compression_config": {
                "method": "l1_unstructured",
                "amount": 0.3
            }
        }
        
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.compress_model.return_value = {
                'model_path': '/path/to/compressed',
                'compression_info': {
                    'compression_ratio': 0.7
                }
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/model/compress",
                headers=auth_headers,
                json=compression_request
            )
            
            assert response.status_code == 200
            assert 'compression_info' in response.json()['data']
    
    def test_model_ensemble(self, auth_headers: Dict[str, str]):
        """测试模型集成API"""
        ensemble_request = {
            "user_id": 1,
            "model_type": "student",
            "model_ids": ["model1", "model2"],
            "weights": [0.6, 0.4]
        }
        
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.create_model_ensemble.return_value = {
                'ensemble_path': '/path/to/ensemble',
                'ensemble_info': {
                    'num_models': 2
                }
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/model/ensemble",
                headers=auth_headers,
                json=ensemble_request
            )
            
            assert response.status_code == 200
            assert 'ensemble_info' in response.json()['data']
    
    def test_get_visualizations(self, auth_headers: Dict[str, str]):
        """测试获取可视化API"""
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_training_status.return_value = {
                'visualizations': {
                    'training_history': '/path/to/history.html',
                    'performance': '/path/to/performance.html'
                }
            }
            mock_get_manager.return_value = mock_manager
            
            response = client.get(
                "/model/visualize/1/student",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert 'visualizations' in response.json()['data']

# 权限测试
class TestAPIPermissions:
    """API权限测试"""
    
    def test_trainer_permissions(self):
        """测试训练权限"""
        # 获取trainer令牌
        response = client.post(
            "/model/token",
            data={
                "username": "trainer",
                "password": "trainer123",
                "scope": "trainer predictor viewer"
            }
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试允许的操作
        response = client.post(
            "/model/train",
            headers=headers,
            json=student_training_request
        )
        assert response.status_code == 200
        
        # 测试禁止的操作
        response = client.post(
            "/model/compress",
            headers=headers,
            json={}
        )
        assert response.status_code == 403
    
    def test_predictor_permissions(self):
        """测试预测权限"""
        # 获取predictor令牌
        response = client.post(
            "/model/token",
            data={
                "username": "predictor",
                "password": "predictor123",
                "scope": "predictor viewer"
            }
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试允许的操作
        response = client.post(
            "/model/predict",
            headers=headers,
            json=prediction_request
        )
        assert response.status_code == 200
        
        # 测试禁止的操作
        response = client.post(
            "/model/train",
            headers=headers,
            json={}
        )
        assert response.status_code == 403

# 错误处理测试
class TestAPIErrorHandling:
    """API错误处理测试"""
    
    def test_invalid_request_format(self, auth_headers: Dict[str, str]):
        """测试无效请求格式"""
        response = client.post(
            "/model/train",
            headers=auth_headers,
            json={}  # 空请求
        )
        assert response.status_code == 422  # 验证错误
    
    def test_not_found(self, auth_headers: Dict[str, str]):
        """测试资源不存在"""
        response = client.get(
            "/model/training/status/999",  # 不存在的用户
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_server_error(self, auth_headers: Dict[str, str]):
        """测试服务器错误"""
        with patch('model_service.api.routes.get_training_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.train_student_model.side_effect = Exception("Internal error")
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/model/train",
                headers=auth_headers,
                json=student_training_request
            )
            assert response.status_code == 500 