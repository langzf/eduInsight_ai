import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import logging
from pathlib import Path
import json

class StudentDataset(Dataset):
    """学生数据集"""
    
    def __init__(self, data: Dict[str, Any], config: Dict[str, Any]):
        """
        初始化数据集
        :param data: 预处理后的数据
        :param config: 配置信息
        """
        self.text_features = torch.tensor(data['text'], dtype=torch.float32)
        self.sequence_features = torch.tensor(data['sequence'], dtype=torch.float32)
        self.weakness_labels = torch.tensor(data['labels']['weaknesses'], dtype=torch.float32)
        self.interest_labels = torch.tensor(data['labels']['interests'], dtype=torch.float32)
        self.path_labels = torch.tensor(data['labels']['path'], dtype=torch.float32)
        self.config = config
        
        # 验证数据维度
        self._validate_data()
    
    def __len__(self) -> int:
        return len(self.text_features)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """获取单个样本"""
        return {
            'text': self.text_features[idx],
            'sequence': self.sequence_features[idx],
            'weaknesses': self.weakness_labels[idx],
            'interests': self.interest_labels[idx],
            'path': self.path_labels[idx]
        }
    
    def _validate_data(self):
        """验证数据维度"""
        try:
            assert len(self.text_features) == len(self.sequence_features), \
                "文本特征和序列特征长度不匹配"
            assert len(self.weakness_labels) == len(self.text_features), \
                "薄弱点标签长度不匹配"
            assert len(self.interest_labels) == len(self.text_features), \
                "兴趣点标签长度不匹配"
            assert len(self.path_labels) == len(self.text_features), \
                "学习路径标签长度不匹配"
            assert self.weakness_labels.shape[1] == self.config['num_weakness_labels'], \
                "薄弱点标签维度不匹配"
            assert self.interest_labels.shape[1] == self.config['num_interest_labels'], \
                "兴趣点标签维度不匹配"
            assert self.path_labels.shape[1] == self.config['num_path_steps'], \
                "学习路径标签维度不匹配"
        except AssertionError as e:
            logging.error(f"数据验证失败: {str(e)}")
            raise

class TeacherDataset(Dataset):
    """教师数据集"""
    
    def __init__(self, data: Dict[str, Any], config: Dict[str, Any]):
        """
        初始化数据集
        :param data: 预处理后的数据
        :param config: 配置信息
        """
        self.content_features = torch.tensor(data['content'], dtype=torch.float32)
        self.student_features = torch.tensor(data['student_data'], dtype=torch.float32)
        self.coverage_labels = torch.tensor(data['labels']['coverage'], dtype=torch.float32)
        self.layer_labels = torch.tensor(data['labels']['student_layers'], dtype=torch.float32)
        self.config = config
        
        # 验证数据维度
        self._validate_data()
    
    def __len__(self) -> int:
        return len(self.content_features)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """获取单个样本"""
        return {
            'content': self.content_features[idx],
            'student_data': self.student_features[idx],
            'coverage': self.coverage_labels[idx],
            'student_layers': self.layer_labels[idx]
        }
    
    def _validate_data(self):
        """验证数据维度"""
        try:
            assert len(self.content_features) == len(self.student_features), \
                "内容特征和学生特征长度不匹配"
            assert len(self.coverage_labels) == len(self.content_features), \
                "覆盖率标签长度不匹配"
            assert len(self.layer_labels) == len(self.content_features), \
                "分层标签长度不匹配"
            assert self.coverage_labels.shape[1] == len(self.config['subjects']), \
                "覆盖率标签维度不匹配"
            assert self.layer_labels.shape[1] == len(self.config['layer_labels']), \
                "分层标签维度不匹配"
        except AssertionError as e:
            logging.error(f"数据验证失败: {str(e)}")
            raise

class DataLoaderFactory:
    """数据加载器工厂"""
    
    @staticmethod
    def create_data_loader(
        data: Dict[str, Any],
        config: Dict[str, Any],
        model_type: str,
        batch_size: int,
        shuffle: bool = True
    ) -> DataLoader:
        """
        创建数据加载器
        :param data: 预处理后的数据
        :param config: 配置信息
        :param model_type: 模型类型 ('student' 或 'teacher')
        :param batch_size: 批次大小
        :param shuffle: 是否打乱数据
        :return: 数据加载器
        """
        try:
            # 选择数据集类
            dataset_class = StudentDataset if model_type == 'student' else TeacherDataset
            
            # 创建数据集
            dataset = dataset_class(data, config)
            
            # 创建数据加载器
            loader = DataLoader(
                dataset,
                batch_size=batch_size,
                shuffle=shuffle,
                num_workers=config.get('num_workers', 2),
                pin_memory=True if torch.cuda.is_available() else False
            )
            
            return loader
            
        except Exception as e:
            logging.error(f"创建数据加载器失败: {str(e)}")
            raise

class DataSaver:
    """数据保存器"""
    
    @staticmethod
    def save_batch(
        batch: Dict[str, torch.Tensor],
        save_dir: str,
        batch_idx: int
    ):
        """
        保存批次数据
        :param batch: 批次数据
        :param save_dir: 保存目录
        :param batch_idx: 批次索引
        """
        try:
            save_path = Path(save_dir) / f"batch_{batch_idx}.pt"
            torch.save(batch, save_path)
        except Exception as e:
            logging.error(f"保存批次数据失败: {str(e)}")
            raise
    
    @staticmethod
    def load_batch(save_dir: str, batch_idx: int) -> Optional[Dict[str, torch.Tensor]]:
        """
        加载批次数据
        :param save_dir: 保存目录
        :param batch_idx: 批次索引
        :return: 批次数据
        """
        try:
            save_path = Path(save_dir) / f"batch_{batch_idx}.pt"
            if save_path.exists():
                return torch.load(save_path)
            return None
        except Exception as e:
            logging.error(f"加载批次数据失败: {str(e)}")
            raise 