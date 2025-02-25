import torch
import numpy as np
from typing import Dict, List, Any, Tuple
import logging
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from pathlib import Path
import json
from datetime import datetime

class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_dir = config.get('metrics_dir', 'metrics')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 创建指标保存目录
        Path(self.metrics_dir).mkdir(parents=True, exist_ok=True)
    
    def evaluate_student_model(self,
                             model: torch.nn.Module,
                             data_loader: torch.utils.data.DataLoader,
                             student_id: int) -> Dict[str, Any]:
        """
        评估学生模型
        :param model: 模型实例
        :param data_loader: 数据加载器
        :param student_id: 学生ID
        :return: 评估结果
        """
        try:
            model.eval()
            all_predictions = {
                'weaknesses': [],
                'interests': [],
                'path': []
            }
            all_labels = {
                'weaknesses': [],
                'interests': [],
                'path': []
            }
            total_loss = 0
            
            with torch.no_grad():
                for batch in data_loader:
                    # 移动数据到设备
                    text_features = batch['text'].to(self.device)
                    sequence_features = batch['sequence'].to(self.device)
                    
                    # 前向传播
                    outputs = model(text_features, sequence_features)
                    
                    # 收集预测和标签
                    for key in ['weaknesses', 'interests', 'path']:
                        all_predictions[key].append(outputs[key].cpu().numpy())
                        all_labels[key].append(batch[key].numpy())
            
            # 计算指标
            metrics = self._calculate_student_metrics(
                {k: np.concatenate(v) for k, v in all_predictions.items()},
                {k: np.concatenate(v) for k, v in all_labels.items()}
            )
            
            # 保存评估结果
            self._save_metrics(metrics, 'student', student_id)
            
            return metrics
            
        except Exception as e:
            logging.error(f"评估学生模型失败: {str(e)}")
            raise
    
    def evaluate_teacher_model(self,
                             model: torch.nn.Module,
                             data_loader: torch.utils.data.DataLoader,
                             teacher_id: int) -> Dict[str, Any]:
        """
        评估教师模型
        :param model: 模型实例
        :param data_loader: 数据加载器
        :param teacher_id: 教师ID
        :return: 评估结果
        """
        try:
            model.eval()
            all_predictions = {
                'coverage': [],
                'layers': []
            }
            all_labels = {
                'coverage': [],
                'layers': []
            }
            total_loss = 0
            
            with torch.no_grad():
                for batch in data_loader:
                    # 移动数据到设备
                    content_features = batch['content'].to(self.device)
                    student_features = batch['student_data'].to(self.device)
                    
                    # 前向传播
                    outputs = model(content_features, student_features)
                    
                    # 收集预测和标签
                    for key in ['coverage', 'layers']:
                        all_predictions[key].append(outputs[key].cpu().numpy())
                        all_labels[key].append(batch[key].numpy())
            
            # 计算指标
            metrics = self._calculate_teacher_metrics(
                {k: np.concatenate(v) for k, v in all_predictions.items()},
                {k: np.concatenate(v) for k, v in all_labels.items()}
            )
            
            # 保存评估结果
            self._save_metrics(metrics, 'teacher', teacher_id)
            
            return metrics
            
        except Exception as e:
            logging.error(f"评估教师模型失败: {str(e)}")
            raise
    
    def _calculate_student_metrics(self,
                                 predictions: Dict[str, np.ndarray],
                                 labels: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """计算学生模型指标"""
        try:
            metrics = {}
            
            # 薄弱点指标
            weakness_preds = (predictions['weaknesses'] > 0.5).astype(int)
            precision, recall, f1, _ = precision_recall_fscore_support(
                labels['weaknesses'],
                weakness_preds,
                average='weighted'
            )
            metrics['weakness'] = {
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1)
            }
            
            # 兴趣点指标
            interest_preds = (predictions['interests'] > 0.5).astype(int)
            precision, recall, f1, _ = precision_recall_fscore_support(
                labels['interests'],
                interest_preds,
                average='weighted'
            )
            metrics['interest'] = {
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1)
            }
            
            # 学习路径指标
            path_preds = np.argmax(predictions['path'], axis=1)
            path_labels = np.argmax(labels['path'], axis=1)
            accuracy = accuracy_score(path_labels, path_preds)
            metrics['path'] = {
                'accuracy': float(accuracy)
            }
            
            # 计算总体指标
            metrics['overall'] = {
                'f1': float((metrics['weakness']['f1'] + 
                           metrics['interest']['f1']) / 2),
                'accuracy': float(accuracy)
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"计算学生模型指标失败: {str(e)}")
            raise
    
    def _calculate_teacher_metrics(self,
                                 predictions: Dict[str, np.ndarray],
                                 labels: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """计算教师模型指标"""
        try:
            metrics = {}
            
            # 内容覆盖率指标
            coverage_preds = np.argmax(predictions['coverage'], axis=1)
            coverage_labels = np.argmax(labels['coverage'], axis=1)
            accuracy = accuracy_score(coverage_labels, coverage_preds)
            metrics['coverage'] = {
                'accuracy': float(accuracy)
            }
            
            # 学生分层指标
            layer_preds = np.argmax(predictions['layers'], axis=1)
            layer_labels = np.argmax(labels['layers'], axis=1)
            precision, recall, f1, _ = precision_recall_fscore_support(
                layer_labels,
                layer_preds,
                average='weighted'
            )
            metrics['layers'] = {
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1)
            }
            
            # 计算总体指标
            metrics['overall'] = {
                'accuracy': float((accuracy + metrics['layers']['f1']) / 2)
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"计算教师模型指标失败: {str(e)}")
            raise
    
    def _save_metrics(self,
                     metrics: Dict[str, Any],
                     model_type: str,
                     user_id: int):
        """保存评估指标"""
        try:
            # 创建保存路径
            save_path = Path(self.metrics_dir) / f"{model_type}_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 添加时间戳
            metrics['timestamp'] = datetime.now().isoformat()
            
            # 保存指标
            with open(save_path / 'metrics.json', 'w') as f:
                json.dump(metrics, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存评估指标失败: {str(e)}")
            raise 