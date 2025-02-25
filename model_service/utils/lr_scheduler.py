import torch
from torch.optim.lr_scheduler import _LRScheduler
from typing import Dict, Any, Optional, List, Union
import logging
import math
import numpy as np
from enum import Enum
import json
from pathlib import Path
from datetime import datetime

class SchedulerType(Enum):
    """调度器类型"""
    STEP = 'step'              # 阶梯式衰减
    COSINE = 'cosine'         # 余弦衰减
    LINEAR = 'linear'         # 线性衰减
    EXPONENTIAL = 'exp'       # 指数衰减
    CYCLIC = 'cyclic'         # 循环调整
    WARMUP = 'warmup'         # 预热调整

class LRSchedulerFactory:
    """学习率调度器工厂"""
    
    @staticmethod
    def create_scheduler(
        optimizer: torch.optim.Optimizer,
        scheduler_type: SchedulerType,
        config: Dict[str, Any]
    ) -> _LRScheduler:
        """
        创建学习率调度器
        :param optimizer: 优化器
        :param scheduler_type: 调度器类型
        :param config: 配置信息
        :return: 学习率调度器
        """
        try:
            if scheduler_type == SchedulerType.STEP:
                return StepLRScheduler(
                    optimizer,
                    step_size=config.get('step_size', 30),
                    gamma=config.get('gamma', 0.1)
                )
            elif scheduler_type == SchedulerType.COSINE:
                return CosineLRScheduler(
                    optimizer,
                    T_max=config.get('T_max', 100),
                    eta_min=config.get('eta_min', 0)
                )
            elif scheduler_type == SchedulerType.LINEAR:
                return LinearLRScheduler(
                    optimizer,
                    total_epochs=config.get('total_epochs', 100)
                )
            elif scheduler_type == SchedulerType.EXPONENTIAL:
                return ExponentialLRScheduler(
                    optimizer,
                    gamma=config.get('gamma', 0.95)
                )
            elif scheduler_type == SchedulerType.CYCLIC:
                return CyclicLRScheduler(
                    optimizer,
                    base_lr=config.get('base_lr', 1e-4),
                    max_lr=config.get('max_lr', 1e-2),
                    step_size=config.get('step_size', 20)
                )
            elif scheduler_type == SchedulerType.WARMUP:
                return WarmupLRScheduler(
                    optimizer,
                    warmup_epochs=config.get('warmup_epochs', 5),
                    total_epochs=config.get('total_epochs', 100),
                    base_scheduler_type=config.get('base_scheduler', SchedulerType.COSINE)
                )
            else:
                raise ValueError(f"不支持的调度器类型: {scheduler_type}")
                
        except Exception as e:
            logging.error(f"创建学习率调度器失败: {str(e)}")
            raise

class StepLRScheduler(_LRScheduler):
    """阶梯式学习率调度器"""
    
    def __init__(self,
                 optimizer: torch.optim.Optimizer,
                 step_size: int,
                 gamma: float = 0.1):
        self.step_size = step_size
        self.gamma = gamma
        super().__init__(optimizer)
    
    def get_lr(self) -> List[float]:
        return [base_lr * self.gamma ** (self.last_epoch // self.step_size)
                for base_lr in self.base_lrs]

class CosineLRScheduler(_LRScheduler):
    """余弦学习率调度器"""
    
    def __init__(self,
                 optimizer: torch.optim.Optimizer,
                 T_max: int,
                 eta_min: float = 0):
        self.T_max = T_max
        self.eta_min = eta_min
        super().__init__(optimizer)
    
    def get_lr(self) -> List[float]:
        return [self.eta_min + (base_lr - self.eta_min) *
                (1 + math.cos(math.pi * self.last_epoch / self.T_max)) / 2
                for base_lr in self.base_lrs]

class LinearLRScheduler(_LRScheduler):
    """线性学习率调度器"""
    
    def __init__(self,
                 optimizer: torch.optim.Optimizer,
                 total_epochs: int):
        self.total_epochs = total_epochs
        super().__init__(optimizer)
    
    def get_lr(self) -> List[float]:
        return [base_lr * (1 - self.last_epoch / self.total_epochs)
                for base_lr in self.base_lrs]

class ExponentialLRScheduler(_LRScheduler):
    """指数学习率调度器"""
    
    def __init__(self,
                 optimizer: torch.optim.Optimizer,
                 gamma: float = 0.95):
        self.gamma = gamma
        super().__init__(optimizer)
    
    def get_lr(self) -> List[float]:
        return [base_lr * self.gamma ** self.last_epoch
                for base_lr in self.base_lrs]

class CyclicLRScheduler(_LRScheduler):
    """循环学习率调度器"""
    
    def __init__(self,
                 optimizer: torch.optim.Optimizer,
                 base_lr: float,
                 max_lr: float,
                 step_size: int):
        self.base_lr = base_lr
        self.max_lr = max_lr
        self.step_size = step_size
        super().__init__(optimizer)
    
    def get_lr(self) -> List[float]:
        cycle = math.floor(1 + self.last_epoch / (2 * self.step_size))
        x = abs(self.last_epoch / self.step_size - 2 * cycle + 1)
        return [self.base_lr + (self.max_lr - self.base_lr) * max(0, (1 - x))
                for _ in self.base_lrs]

class WarmupLRScheduler(_LRScheduler):
    """预热学习率调度器"""
    
    def __init__(self,
                 optimizer: torch.optim.Optimizer,
                 warmup_epochs: int,
                 total_epochs: int,
                 base_scheduler_type: SchedulerType = SchedulerType.COSINE):
        self.warmup_epochs = warmup_epochs
        self.total_epochs = total_epochs
        self.base_scheduler_type = base_scheduler_type
        
        # 创建基础调度器
        self.base_scheduler = LRSchedulerFactory.create_scheduler(
            optimizer,
            base_scheduler_type,
            {'total_epochs': total_epochs - warmup_epochs}
        )
        
        super().__init__(optimizer)
    
    def get_lr(self) -> List[float]:
        if self.last_epoch < self.warmup_epochs:
            # 线性预热
            return [base_lr * (self.last_epoch + 1) / self.warmup_epochs
                    for base_lr in self.base_lrs]
        else:
            # 使用基础调度器
            self.base_scheduler.last_epoch = self.last_epoch - self.warmup_epochs
            return self.base_scheduler.get_lr()

class LRMonitor:
    """学习率监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.history = []
        self.log_dir = Path(config.get('log_dir', 'lr_logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def step(self,
             epoch: int,
             lr: float,
             metrics: Optional[Dict[str, float]] = None):
        """记录学习率和指标"""
        record = {
            'epoch': epoch,
            'lr': lr,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        self.history.append(record)
    
    def save_history(self,
                    user_id: int,
                    model_type: str):
        """保存历史记录"""
        try:
            save_path = self.log_dir / f"{model_type}_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            with open(save_path / 'lr_history.json', 'w') as f:
                json.dump({
                    'history': self.history,
                    'config': self.config
                }, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存学习率历史记录失败: {str(e)}")
            raise
    
    def get_best_lr(self) -> float:
        """获取最佳学习率"""
        if not self.history or not self.history[0].get('metrics'):
            return self.config.get('default_lr', 0.001)
        
        # 根据主要指标选择最佳学习率
        main_metric = self.config.get('main_metric', 'loss')
        best_record = min(
            self.history,
            key=lambda x: x['metrics'].get(main_metric, float('inf'))
        )
        return best_record['lr'] 