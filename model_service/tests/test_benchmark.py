import pytest
import time
import torch
from typing import Dict, Any
import numpy as np
from statistics import mean
import json
from pathlib import Path

from model_service.models.student_model import StudentModel
from model_service.models.teacher_model import TeacherModel
from model_service.utils.train_manager import TrainingManager

class ModelBenchmark:
    """模型基准测试"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # 初始化结果记录
        self.results = {
            'model_inference': [],
            'data_processing': [],
            'training_speed': [],
            'memory_usage': []
        }
    
    def benchmark_model_inference(self, model: torch.nn.Module, n_runs: int = 100):
        """测试模型推理性能"""
        # 准备测试数据
        if isinstance(model, StudentModel):
            input_data = {
                'text': torch.randn(1, 10),
                'sequence': torch.randn(1, 3)
            }
        else:
            input_data = {
                'content': torch.randn(1, 10),
                'student_data': torch.randn(1, 4)
            }
        
        # 预热
        for _ in range(10):
            _ = model(**input_data)
        
        # 测试推理时间
        times = []
        torch.cuda.synchronize()
        for _ in range(n_runs):
            start = time.perf_counter()
            _ = model(**input_data)
            torch.cuda.synchronize()
            times.append(time.perf_counter() - start)
        
        self.results['model_inference'].append({
            'model_type': model.__class__.__name__,
            'mean_time': mean(times),
            'std_time': np.std(times),
            'min_time': min(times),
            'max_time': max(times)
        })
    
    def benchmark_data_processing(self, manager: TrainingManager, n_runs: int = 100):
        """测试数据处理性能"""
        # 准备测试数据
        test_data = {
            "text": ["内容" + str(i) for i in range(100)],
            "sequence": [[i, i+1, i+2] for i in range(100)],
            "labels": {
                "weaknesses": [[1, 0] for _ in range(100)],
                "interests": [[0, 1] for _ in range(100)],
                "path": [[0.7, 0.3] for _ in range(100)]
            }
        }
        
        # 测试预处理时间
        times = []
        for _ in range(n_runs):
            start = time.perf_counter()
            _ = manager._prepare_data_loader(test_data)
            times.append(time.perf_counter() - start)
        
        self.results['data_processing'].append({
            'operation': 'data_loading',
            'mean_time': mean(times),
            'std_time': np.std(times),
            'min_time': min(times),
            'max_time': max(times)
        })
    
    def benchmark_training_speed(self, manager: TrainingManager):
        """测试训练速度"""
        # 准备测试数据
        test_data = {
            "text": ["内容" + str(i) for i in range(1000)],
            "sequence": [[i, i+1, i+2] for i in range(1000)],
            "labels": {
                "weaknesses": [[1, 0] for _ in range(1000)],
                "interests": [[0, 1] for _ in range(1000)],
                "path": [[0.7, 0.3] for _ in range(1000)]
            }
        }
        
        # 测试不同批次大小
        batch_sizes = [16, 32, 64, 128]
        for batch_size in batch_sizes:
            manager.batch_size = batch_size
            model = StudentModel(manager.config)
            
            start = time.perf_counter()
            _ = manager.train_student_model(model, 1, test_data)
            duration = time.perf_counter() - start
            
            self.results['training_speed'].append({
                'batch_size': batch_size,
                'total_time': duration,
                'samples_per_second': len(test_data['text']) / duration
            })
    
    def benchmark_memory_usage(self, manager: TrainingManager):
        """测试内存使用"""
        import psutil
        process = psutil.Process()
        
        # 测试不同数据大小
        sizes = [100, 1000, 10000]
        for size in sizes:
            test_data = {
                "text": ["内容" + str(i) for i in range(size)],
                "sequence": [[i, i+1, i+2] for i in range(size)],
                "labels": {
                    "weaknesses": [[1, 0] for _ in range(size)],
                    "interests": [[0, 1] for _ in range(size)],
                    "path": [[0.7, 0.3] for _ in range(size)]
                }
            }
            
            # 记录内存使用
            initial_memory = process.memory_info().rss
            _ = manager._prepare_data_loader(test_data)
            final_memory = process.memory_info().rss
            
            self.results['memory_usage'].append({
                'data_size': size,
                'memory_increase': (final_memory - initial_memory) / 1024 / 1024,  # MB
                'total_memory': final_memory / 1024 / 1024  # MB
            })
    
    def save_results(self):
        """保存基准测试结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.results_dir / f"benchmark_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return str(results_file)

# 基准测试
@pytest.mark.benchmark
class TestModelBenchmark:
    """模型基准测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试环境设置"""
        self.config = {
            'model_dir': 'benchmark_models',
            'batch_size': 32,
            'learning_rate': 0.001
        }
        self.benchmark = ModelBenchmark(self.config)
        self.manager = TrainingManager(self.config)
        
        yield
        
        # 保存结果
        self.benchmark.save_results()
    
    def test_model_inference_performance(self):
        """测试模型推理性能"""
        # 测试学生模型
        student_model = StudentModel(self.config)
        self.benchmark.benchmark_model_inference(student_model)
        
        # 测试教师模型
        teacher_model = TeacherModel(self.config)
        self.benchmark.benchmark_model_inference(teacher_model)
        
        # 验证结果
        results = self.benchmark.results['model_inference']
        assert len(results) == 2
        assert all(r['mean_time'] < 0.1 for r in results)  # 平均推理时间小于100ms
    
    def test_data_processing_performance(self):
        """测试数据处理性能"""
        self.benchmark.benchmark_data_processing(self.manager)
        
        results = self.benchmark.results['data_processing']
        assert len(results) > 0
        assert all(r['mean_time'] < 1.0 for r in results)  # 平均处理时间小于1秒
    
    def test_training_speed(self):
        """测试训练速度"""
        self.benchmark.benchmark_training_speed(self.manager)
        
        results = self.benchmark.results['training_speed']
        assert len(results) > 0
        assert all(r['samples_per_second'] > 10 for r in results)  # 每秒处理10个以上样本
    
    def test_memory_usage(self):
        """测试内存使用"""
        self.benchmark.benchmark_memory_usage(self.manager)
        
        results = self.benchmark.results['memory_usage']
        assert len(results) > 0
        assert all(r['memory_increase'] < 1000 for r in results)  # 内存增加小于1GB 