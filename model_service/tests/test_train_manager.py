import pytest
import torch
from unittest.mock import Mock, patch
from typing import Dict, Any
from model_service.utils.train_manager import TrainingManager
from model_service.models.student_model import StudentModel
from model_service.models.teacher_model import TeacherModel

# 测试配置
@pytest.fixture
def config() -> Dict[str, Any]:
    return {
        'model_dir': 'test_models',
        'max_epochs': 2,
        'batch_size': 2,
        'learning_rate': 0.001,
        'subjects': ['math', 'physics'],
        'weakness_labels': ['concept', 'practice'],
        'interest_labels': ['theory', 'experiment'],
        'path_steps': ['basic', 'advanced'],
        'layer_labels': ['需要关注', '一般', '优秀']
    }

# 测试数据
@pytest.fixture
def training_data() -> Dict[str, Any]:
    return {
        'text': ['学习内容1', '学习内容2'],
        'sequence': [[1, 2, 3], [4, 5, 6]],
        'labels': {
            'weaknesses': [[1, 0], [0, 1]],
            'interests': [[0, 1], [1, 0]],
            'path': [[0.7, 0.3], [0.4, 0.6]]
        }
    }

@pytest.fixture
def teacher_data() -> Dict[str, Any]:
    return {
        'content': {
            'plans': ['教学计划1', '教学计划2'],
            'recordings': ['课堂记录1', '课堂记录2'],
            'feedback': ['反馈1', '反馈2']
        },
        'student_data': [
            {
                'average_score': 85,
                'attendance_rate': 0.9,
                'participation_rate': 0.8,
                'homework_completion_rate': 0.95
            },
            {
                'average_score': 75,
                'attendance_rate': 0.8,
                'participation_rate': 0.7,
                'homework_completion_rate': 0.85
            }
        ],
        'labels': {
            'coverage': {'math': 0.8, 'physics': 0.7},
            'student_layers': [0.2, 0.5, 0.3]
        }
    }

# 训练管理器测试
class TestTrainingManager:
    
    @pytest.mark.asyncio
    async def test_train_student_model(self,
                                     config: Dict[str, Any],
                                     training_data: Dict[str, Any]):
        """测试学生模型训练"""
        # 初始化
        manager = TrainingManager(config)
        model = StudentModel(config)
        
        # 执行训练
        result = await manager.train_student_model(
            model,
            student_id=1,
            training_data=training_data
        )
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'model_path' in result
        assert 'training_info' in result
        
        # 验证训练状态
        status = manager.get_training_status(1)
        assert status['status'] == 'completed'
        assert 'progress' in status
        assert 'metrics' in status
    
    @pytest.mark.asyncio
    async def test_train_teacher_model(self,
                                     config: Dict[str, Any],
                                     teacher_data: Dict[str, Any]):
        """测试教师模型训练"""
        # 初始化
        manager = TrainingManager(config)
        model = TeacherModel(config)
        
        # 执行训练
        result = await manager.train_teacher_model(
            model,
            teacher_id=1,
            training_data=teacher_data
        )
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'model_path' in result
        assert 'training_info' in result
        
        # 验证训练状态
        status = manager.get_training_status(1)
        assert status['status'] == 'completed'
        assert 'progress' in status
        assert 'metrics' in status
    
    @pytest.mark.asyncio
    async def test_early_stopping(self,
                                config: Dict[str, Any],
                                training_data: Dict[str, Any]):
        """测试早停机制"""
        # 修改配置
        config['patience'] = 1
        config['min_delta'] = 0.1
        
        # 初始化
        manager = TrainingManager(config)
        model = StudentModel(config)
        
        # 执行训练
        result = await manager.train_student_model(
            model,
            student_id=1,
            training_data=training_data
        )
        
        # 验证早停
        status = manager.get_training_status(1)
        assert status['training_summary']['stopped_early']
    
    def test_model_save_load(self,
                            config: Dict[str, Any]):
        """测试模型保存和加载"""
        # 初始化
        manager = TrainingManager(config)
        model = StudentModel(config)
        
        # 保存模型
        manager._save_model(
            model,
            user_id=1,
            epoch=0,
            loss=0.5
        )
        
        # 验证模型文件
        model_path = f"{config['model_dir']}/student_1"
        assert Path(model_path).exists()
    
    @pytest.mark.asyncio
    async def test_distributed_training(self,
                                     config: Dict[str, Any],
                                     training_data: Dict[str, Any]):
        """测试分布式训练"""
        # 修改配置
        config['world_size'] = 2
        
        # 初始化
        manager = TrainingManager(config)
        model = StudentModel(config)
        
        # 执行分布式训练
        result = await manager.train_distributed(
            model,
            user_id=1,
            training_data=training_data
        )
        
        # 验证结果
        assert 'merged_results' in result
        assert result['merged_results']['training_info']['world_size'] == 2

# 数据处理测试
class TestDataProcessing:
    
    @pytest.mark.asyncio
    async def test_student_data_preprocessing(self,
                                           config: Dict[str, Any],
                                           training_data: Dict[str, Any]):
        """测试学生数据预处理"""
        manager = TrainingManager(config)
        
        # 预处理数据
        processed = await manager._preprocess_student_data(training_data)
        
        # 验证结果
        assert isinstance(processed['text'], torch.Tensor)
        assert isinstance(processed['sequence'], torch.Tensor)
        assert isinstance(processed['weaknesses'], torch.Tensor)
        assert isinstance(processed['interests'], torch.Tensor)
        assert isinstance(processed['path'], torch.Tensor)
    
    @pytest.mark.asyncio
    async def test_teacher_data_preprocessing(self,
                                           config: Dict[str, Any],
                                           teacher_data: Dict[str, Any]):
        """测试教师数据预处理"""
        manager = TrainingManager(config)
        
        # 预处理数据
        processed = await manager._preprocess_teacher_data(teacher_data)
        
        # 验证结果
        assert isinstance(processed['content'], torch.Tensor)
        assert isinstance(processed['student_data'], torch.Tensor)
        assert isinstance(processed['coverage'], torch.Tensor)
        assert isinstance(processed['student_layers'], torch.Tensor)

# 模型评估测试
class TestModelEvaluation:
    
    def test_student_model_predictions(self,
                                     config: Dict[str, Any]):
        """测试学生模型预测"""
        manager = TrainingManager(config)
        model = StudentModel(config)
        
        # 创建测试输入
        inputs = {
            'text': torch.randn(1, 10),
            'sequence': torch.randn(1, 3)
        }
        
        # 执行预测
        outputs = model(**inputs)
        predictions = manager._postprocess_student_predictions(outputs)
        
        # 验证结果
        assert 'weaknesses' in predictions
        assert 'interests' in predictions
        assert 'learning_path' in predictions
    
    def test_teacher_model_predictions(self,
                                     config: Dict[str, Any]):
        """测试教师模型预测"""
        manager = TrainingManager(config)
        model = TeacherModel(config)
        
        # 创建测试输入
        inputs = {
            'content': torch.randn(1, 10),
            'student_data': torch.randn(1, 4)
        }
        
        # 执行预测
        outputs = model(**inputs)
        predictions = manager._postprocess_teacher_predictions(outputs)
        
        # 验证结果
        assert 'coverage' in predictions
        assert 'student_layers' in predictions
        assert 'suggestions' in predictions

# 错误处理测试
class TestErrorHandling:
    
    @pytest.mark.asyncio
    async def test_invalid_model_type(self,
                                    config: Dict[str, Any],
                                    training_data: Dict[str, Any]):
        """测试无效模型类型"""
        manager = TrainingManager(config)
        
        with pytest.raises(ValueError):
            await manager.train_distributed(
                None,  # 无效模型
                user_id=1,
                training_data=training_data
            )
    
    @pytest.mark.asyncio
    async def test_invalid_data_format(self,
                                     config: Dict[str, Any]):
        """测试无效数据格式"""
        manager = TrainingManager(config)
        model = StudentModel(config)
        
        with pytest.raises(Exception):
            await manager.train_student_model(
                model,
                student_id=1,
                training_data={}  # 空数据
            ) 