import pytest
import asyncio
from typing import Dict, Any
from fastapi.testclient import TestClient
import torch
import json
import os
from pathlib import Path

from model_service.main import app
from model_service.models.student_model import StudentModel
from model_service.models.teacher_model import TeacherModel
from model_service.utils.train_manager import TrainingManager
from model_service.utils.data_loader import DataLoaderFactory

# 测试客户端
client = TestClient(app)

class TestModelIntegration:
    """模型服务集成测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试环境设置"""
        # 创建测试目录
        self.test_dir = Path("test_integration")
        self.test_dir.mkdir(exist_ok=True)
        
        # 配置
        self.config = {
            'model_dir': str(self.test_dir / 'models'),
            'data_dir': str(self.test_dir / 'data'),
            'cache_dir': str(self.test_dir / 'cache'),
            'max_epochs': 2,
            'batch_size': 2,
            'learning_rate': 0.001
        }
        
        # 创建训练管理器
        self.manager = TrainingManager(self.config)
        
        yield
        
        # 清理测试目录
        import shutil
        shutil.rmtree(self.test_dir)
    
    async def test_complete_training_workflow(self):
        """测试完整训练流程"""
        # 1. 准备训练数据
        training_data = {
            "text": ["内容1", "内容2"],
            "sequence": [[1, 2, 3], [4, 5, 6]],
            "labels": {
                "weaknesses": [[1, 0], [0, 1]],
                "interests": [[0, 1], [1, 0]],
                "path": [[0.7, 0.3], [0.4, 0.6]]
            }
        }
        
        # 2. 训练学生模型
        model = StudentModel(self.config)
        result = await self.manager.train_student_model(
            model,
            student_id=1,
            training_data=training_data
        )
        
        assert result['status'] == 'success'
        model_path = result['model_path']
        assert Path(model_path).exists()
        
        # 3. 量化模型
        quant_result = self.manager.quantize_trained_model(
            model,
            user_id=1,
            quant_type='dynamic'
        )
        
        assert 'model_path' in quant_result
        assert 'quantization_info' in quant_result
        
        # 4. 执行预测
        input_data = {
            "text": "测试内容",
            "sequence": [1, 2, 3]
        }
        predictions = model(
            torch.tensor([input_data["text"]]),
            torch.tensor([input_data["sequence"]])
        )
        
        processed = self.manager._postprocess_student_predictions(predictions)
        assert 'weaknesses' in processed
        assert 'interests' in processed
        assert 'learning_path' in processed
    
    async def test_model_ensemble_workflow(self):
        """测试模型集成流程"""
        # 1. 准备多个模型
        models = []
        for i in range(3):
            model = StudentModel(self.config)
            result = await self.manager.train_student_model(
                model,
                student_id=i+1,
                training_data={
                    "text": [f"内容{j}" for j in range(5)],
                    "sequence": [[j, j+1, j+2] for j in range(5)],
                    "labels": {
                        "weaknesses": [[1, 0] for _ in range(5)],
                        "interests": [[0, 1] for _ in range(5)],
                        "path": [[0.7, 0.3] for _ in range(5)]
                    }
                }
            )
            assert result['status'] == 'success'
            models.append(model)
        
        # 2. 创建集成
        weights = [0.4, 0.3, 0.3]
        ensemble_result = self.manager.create_model_ensemble(
            models,
            weights=weights,
            user_id=1
        )
        
        assert 'ensemble_path' in ensemble_result
        assert 'ensemble_info' in ensemble_result
        
        # 3. 使用集成模型预测
        input_data = {
            "text": torch.tensor([[1.0] * 10]),
            "sequence": torch.tensor([[1, 2, 3]])
        }
        predictions = self.manager.ensemble_predict(
            input_data,
            ensemble_type='weighted'
        )
        
        assert isinstance(predictions, dict)
        assert all(k in predictions for k in ['weaknesses', 'interests', 'learning_path'])
    
    async def test_data_processing_pipeline(self):
        """测试数据处理流程"""
        # 1. 准备原始数据
        raw_data = {
            "text": ["学习内容1", "学习内容2"],
            "sequence": [[1, 2, 3], [4, 5, 6]],
            "labels": {
                "weaknesses": [[1, 0], [0, 1]],
                "interests": [[0, 1], [1, 0]],
                "path": [[0.7, 0.3], [0.4, 0.6]]
            }
        }
        
        # 2. 预处理数据
        processed_data = await self.manager._preprocess_student_data(raw_data)
        
        assert isinstance(processed_data['text'], torch.Tensor)
        assert isinstance(processed_data['sequence'], torch.Tensor)
        assert isinstance(processed_data['weaknesses'], torch.Tensor)
        
        # 3. 创建数据加载器
        loader = self.manager._prepare_data_loader(processed_data)
        
        # 4. 验证批次数据
        batch = next(iter(loader))
        assert isinstance(batch, dict)
        assert all(isinstance(v, torch.Tensor) for v in batch.values())
    
    async def test_model_compression_pipeline(self):
        """测试模型压缩流程"""
        # 1. 训练模型
        model = StudentModel(self.config)
        result = await self.manager.train_student_model(
            model,
            student_id=1,
            training_data={
                "text": ["内容1", "内容2"],
                "sequence": [[1, 2, 3], [4, 5, 6]],
                "labels": {
                    "weaknesses": [[1, 0], [0, 1]],
                    "interests": [[0, 1], [1, 0]],
                    "path": [[0.7, 0.3], [0.4, 0.6]]
                }
            }
        )
        
        assert result['status'] == 'success'
        
        # 2. 执行不同类型的压缩
        compression_types = ['pruning', 'distillation', 'quantization']
        for comp_type in compression_types:
            result = self.manager.compress_model(
                model,
                user_id=1,
                compression_type=comp_type,
                compression_config={
                    'method': 'l1_unstructured',
                    'amount': 0.3
                }
            )
            
            assert 'model_path' in result
            assert 'compression_info' in result
            assert Path(result['model_path']).exists() 