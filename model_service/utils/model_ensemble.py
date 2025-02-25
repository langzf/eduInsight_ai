import torch
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
import logging
from pathlib import Path
import json
from datetime import datetime
from copy import deepcopy

class EnsembleType:
    """集成类型"""
    VOTING = 'voting'          # 投票集成
    AVERAGING = 'averaging'    # 平均集成
    WEIGHTED = 'weighted'      # 加权集成
    STACKING = 'stacking'     # 堆叠集成

class ModelEnsemble:
    """模型集成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.ensemble_dir = Path(config.get('ensemble_dir', 'ensemble_models'))
        
        # 创建集成模型目录
        self.ensemble_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化模型列表
        self.models: List[torch.nn.Module] = []
        self.weights: Optional[List[float]] = None
    
    def add_model(self,
                 model: torch.nn.Module,
                 weight: float = 1.0):
        """
        添加模型到集成
        :param model: 模型实例
        :param weight: 模型权重
        """
        try:
            model.eval()
            model.to(self.device)
            self.models.append(model)
            
            # 更新权重
            if self.weights is None:
                self.weights = [1.0]
            else:
                self.weights.append(weight)
                # 归一化权重
                total = sum(self.weights)
                self.weights = [w/total for w in self.weights]
                
        except Exception as e:
            logging.error(f"添加模型失败: {str(e)}")
            raise
    
    def predict(self,
               inputs: Dict[str, torch.Tensor],
               ensemble_type: str = EnsembleType.WEIGHTED) -> Dict[str, torch.Tensor]:
        """
        集成预测
        :param inputs: 输入数据
        :param ensemble_type: 集成类型
        :return: 预测结果
        """
        try:
            if not self.models:
                raise ValueError("没有可用的模型进行集成")
            
            # 获取所有模型的预测
            predictions = []
            with torch.no_grad():
                for model in self.models:
                    pred = model(**inputs)
                    predictions.append(pred)
            
            # 根据集成类型合并预测
            if ensemble_type == EnsembleType.VOTING:
                return self._voting_ensemble(predictions)
            elif ensemble_type == EnsembleType.AVERAGING:
                return self._averaging_ensemble(predictions)
            elif ensemble_type == EnsembleType.WEIGHTED:
                return self._weighted_ensemble(predictions)
            elif ensemble_type == EnsembleType.STACKING:
                return self._stacking_ensemble(predictions, inputs)
            else:
                raise ValueError(f"不支持的集成类型: {ensemble_type}")
                
        except Exception as e:
            logging.error(f"集成预测失败: {str(e)}")
            raise
    
    def _voting_ensemble(self,
                        predictions: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """投票集成"""
        try:
            ensemble_pred = {}
            for key in predictions[0].keys():
                # 对于分类任务使用众数
                if predictions[0][key].dtype == torch.long:
                    stacked = torch.stack([p[key] for p in predictions])
                    ensemble_pred[key] = torch.mode(stacked, dim=0).values
                # 对于二分类任务使用阈值
                elif predictions[0][key].shape[-1] == 1:
                    stacked = torch.stack([p[key] for p in predictions])
                    mean_pred = torch.mean(stacked, dim=0)
                    ensemble_pred[key] = (mean_pred > 0.5).float()
                # 对于多分类任务使用argmax
                else:
                    stacked = torch.stack([p[key] for p in predictions])
                    mean_pred = torch.mean(stacked, dim=0)
                    ensemble_pred[key] = torch.argmax(mean_pred, dim=-1)
            
            return ensemble_pred
            
        except Exception as e:
            logging.error(f"投票集成失败: {str(e)}")
            raise
    
    def _averaging_ensemble(self,
                          predictions: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """平均集成"""
        try:
            ensemble_pred = {}
            for key in predictions[0].keys():
                stacked = torch.stack([p[key] for p in predictions])
                ensemble_pred[key] = torch.mean(stacked, dim=0)
            
            return ensemble_pred
            
        except Exception as e:
            logging.error(f"平均集成失败: {str(e)}")
            raise
    
    def _weighted_ensemble(self,
                         predictions: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """加权集成"""
        try:
            if not self.weights:
                return self._averaging_ensemble(predictions)
            
            ensemble_pred = {}
            weights = torch.tensor(self.weights, device=self.device)
            
            for key in predictions[0].keys():
                stacked = torch.stack([p[key] for p in predictions])
                weighted_sum = torch.sum(
                    stacked * weights.view(-1, 1, 1),
                    dim=0
                )
                ensemble_pred[key] = weighted_sum
            
            return ensemble_pred
            
        except Exception as e:
            logging.error(f"加权集成失败: {str(e)}")
            raise
    
    def _stacking_ensemble(self,
                         predictions: List[Dict[str, torch.Tensor]],
                         inputs: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """堆叠集成"""
        try:
            # 获取所有模型的预测作为特征
            stacking_features = {}
            for key in predictions[0].keys():
                stacked = torch.stack([p[key] for p in predictions], dim=1)
                stacking_features[key] = stacked
            
            # 如果有元模型，使用元模型进行最终预测
            if hasattr(self, 'meta_model'):
                meta_inputs = {
                    **inputs,
                    'ensemble_predictions': stacking_features
                }
                return self.meta_model(**meta_inputs)
            
            # 否则使用加权平均
            return self._weighted_ensemble(predictions)
            
        except Exception as e:
            logging.error(f"堆叠集成失败: {str(e)}")
            raise
    
    def evaluate_ensemble(self,
                        eval_data: torch.utils.data.DataLoader,
                        ensemble_type: str = EnsembleType.WEIGHTED) -> Dict[str, Any]:
        """
        评估集成模型
        :param eval_data: 评估数据
        :param ensemble_type: 集成类型
        :return: 评估结果
        """
        try:
            all_predictions = []
            all_labels = []
            
            for batch in eval_data:
                # 获取输入和标签
                inputs = {k: v for k, v in batch.items() if k not in ['labels']}
                labels = batch['labels']
                
                # 集成预测
                predictions = self.predict(inputs, ensemble_type)
                
                all_predictions.append(predictions)
                all_labels.append(labels)
            
            # 计算评估指标
            metrics = self._calculate_metrics(all_predictions, all_labels)
            
            return metrics
            
        except Exception as e:
            logging.error(f"评估集成模型失败: {str(e)}")
            raise
    
    def _calculate_metrics(self,
                         predictions: List[Dict[str, torch.Tensor]],
                         labels: List[Dict[str, torch.Tensor]]) -> Dict[str, float]:
        """计算评估指标"""
        try:
            metrics = {}
            
            # 合并所有批次的预测和标签
            merged_pred = {
                k: torch.cat([p[k] for p in predictions])
                for k in predictions[0].keys()
            }
            merged_labels = {
                k: torch.cat([l[k] for l in labels])
                for k in labels[0].keys()
            }
            
            # 计算每个任务的指标
            for key in merged_pred.keys():
                task_metrics = {}
                
                # 分类任务
                if merged_pred[key].shape[-1] > 1:
                    task_metrics['accuracy'] = (
                        torch.argmax(merged_pred[key], dim=-1) ==
                        torch.argmax(merged_labels[key], dim=-1)
                    ).float().mean().item()
                # 回归任务
                else:
                    task_metrics['mse'] = torch.nn.functional.mse_loss(
                        merged_pred[key],
                        merged_labels[key]
                    ).item()
                
                metrics[key] = task_metrics
            
            return metrics
            
        except Exception as e:
            logging.error(f"计算评估指标失败: {str(e)}")
            raise
    
    def save_ensemble(self,
                     ensemble_info: Dict[str, Any],
                     user_id: int,
                     model_type: str) -> str:
        """
        保存集成模型
        :param ensemble_info: 集成信息
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 保存路径
        """
        try:
            # 创建保存目录
            save_path = self.ensemble_dir / f"{model_type}_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 保存每个模型
            model_paths = []
            for i, model in enumerate(self.models):
                model_path = save_path / f"model_{i}.pt"
                torch.save(model.state_dict(), model_path)
                model_paths.append(str(model_path))
            
            # 保存集成信息
            info = {
                **ensemble_info,
                'model_paths': model_paths,
                'weights': self.weights,
                'timestamp': datetime.now().isoformat()
            }
            
            info_path = save_path / 'ensemble_info.json'
            with open(info_path, 'w') as f:
                json.dump(info, f, indent=2)
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"保存集成模型失败: {str(e)}")
            raise
    
    @classmethod
    def load_ensemble(cls,
                     config: Dict[str, Any],
                     model_class: type,
                     save_path: Union[str, Path]) -> 'ModelEnsemble':
        """
        加载集成模型
        :param config: 配置信息
        :param model_class: 模型类
        :param save_path: 保存路径
        :return: 集成模型实例
        """
        try:
            save_path = Path(save_path)
            
            # 加载集成信息
            with open(save_path / 'ensemble_info.json', 'r') as f:
                info = json.load(f)
            
            # 创建集成实例
            ensemble = cls(config)
            
            # 加载每个模型
            for model_path in info['model_paths']:
                model = model_class(config)
                model.load_state_dict(torch.load(model_path))
                ensemble.add_model(model)
            
            # 设置权重
            if info.get('weights'):
                ensemble.weights = info['weights']
            
            return ensemble
            
        except Exception as e:
            logging.error(f"加载集成模型失败: {str(e)}")
            raise 