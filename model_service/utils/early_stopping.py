import numpy as np
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json
from datetime import datetime

class EarlyStoppingMode(Enum):
    """早停模式"""
    MIN = 'min'  # 监控指标越小越好
    MAX = 'max'  # 监控指标越大越好

class EarlyStopping:
    """早停机制"""
    
    def __init__(self,
                 config: Dict[str, Any],
                 mode: EarlyStoppingMode = EarlyStoppingMode.MIN):
        """
        初始化早停器
        :param config: 配置信息
        :param mode: 早停模式
        """
        self.patience = config.get('patience', 5)
        self.min_delta = config.get('min_delta', 1e-4)
        self.mode = mode
        self.baseline = config.get('baseline', None)
        self.restore_best = config.get('restore_best', True)
        
        # 初始化状态
        self.counter = 0
        self.best_score = None
        self.best_epoch = 0
        self.early_stop = False
        self.history = []
        
        # 用于保存验证指标
        self.validation_metrics = []
    
    def __call__(self,
                 epoch: int,
                 current_score: float,
                 model_state: Dict[str, Any],
                 metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        检查是否应该早停
        :param epoch: 当前epoch
        :param current_score: 当前分数
        :param model_state: 模型状态
        :param metrics: 其他指标
        :return: 是否应该停止
        """
        try:
            score = current_score
            
            # 记录历史
            self.history.append({
                'epoch': epoch,
                'score': score,
                'metrics': metrics
            })
            
            # 检查基线
            if self.baseline is not None:
                if self.mode == EarlyStoppingMode.MIN and score > self.baseline:
                    return False
                if self.mode == EarlyStoppingMode.MAX and score < self.baseline:
                    return False
            
            # 第一次记录
            if self.best_score is None:
                self._update_best(score, epoch, model_state)
                return False
            
            # 检查是否改善
            if self._is_improved(score):
                self._update_best(score, epoch, model_state)
                self.counter = 0
            else:
                self.counter += 1
            
            # 检查是否应该停止
            if self.counter >= self.patience:
                self.early_stop = True
                logging.info(f"触发早停: {self.patience} epochs 未改善")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"早停检查失败: {str(e)}")
            return False
    
    def _is_improved(self, score: float) -> bool:
        """检查分数是否改善"""
        if self.mode == EarlyStoppingMode.MIN:
            return score < (self.best_score - self.min_delta)
        return score > (self.best_score + self.min_delta)
    
    def _update_best(self,
                    score: float,
                    epoch: int,
                    model_state: Dict[str, Any]):
        """更新最佳状态"""
        self.best_score = score
        self.best_epoch = epoch
        if self.restore_best:
            self.best_state = model_state.copy()
    
    def get_best_state(self) -> Optional[Dict[str, Any]]:
        """获取最佳模型状态"""
        return self.best_state if self.restore_best else None
    
    def get_training_summary(self) -> Dict[str, Any]:
        """获取训练总结"""
        return {
            'best_score': float(self.best_score) if self.best_score is not None else None,
            'best_epoch': self.best_epoch,
            'total_epochs': len(self.history),
            'stopped_early': self.early_stop,
            'history': self.history
        }
    
    def add_validation_metrics(self, metrics: Dict[str, Any]):
        """添加验证指标"""
        self.validation_metrics.append(metrics)
    
    def get_validation_trend(self) -> Dict[str, List[float]]:
        """获取验证指标趋势"""
        if not self.validation_metrics:
            return {}
        
        trends = {}
        metrics = self.validation_metrics[0].keys()
        
        for metric in metrics:
            trends[metric] = [m[metric] for m in self.validation_metrics]
        
        return trends
    
    def should_stop_on_baseline(self, score: float) -> bool:
        """检查是否应该基于基线停止"""
        if self.baseline is None:
            return False
            
        if self.mode == EarlyStoppingMode.MIN:
            return score > self.baseline
        return score < self.baseline
    
    def reset(self):
        """重置状态"""
        self.counter = 0
        self.best_score = None
        self.best_epoch = 0
        self.early_stop = False
        self.history = []
        self.validation_metrics = [] 