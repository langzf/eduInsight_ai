import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from pathlib import Path
import json
from datetime import datetime
import numpy as np
from copy import deepcopy

class CompressionType:
    """压缩类型"""
    PRUNING = 'pruning'          # 剪枝
    DISTILLATION = 'distillation'  # 知识蒸馏
    QUANTIZATION = 'quantization'  # 量化
    STRUCTURE = 'structure'       # 结构压缩

class ModelCompressor:
    """模型压缩器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.compressed_dir = Path(config.get('compressed_dir', 'compressed_models'))
        
        # 创建压缩模型目录
        self.compressed_dir.mkdir(parents=True, exist_ok=True)
    
    def compress_model(self,
                      model: nn.Module,
                      compression_type: str,
                      compression_config: Dict[str, Any],
                      training_data: Optional[torch.utils.data.DataLoader] = None,
                      teacher_model: Optional[nn.Module] = None) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        压缩模型
        :param model: 原始模型
        :param compression_type: 压缩类型
        :param compression_config: 压缩配置
        :param training_data: 训练数据
        :param teacher_model: 教师模型(用于知识蒸馏)
        :return: (压缩后的模型, 压缩信息)
        """
        try:
            model_copy = deepcopy(model)
            
            if compression_type == CompressionType.PRUNING:
                return self._prune_model(model_copy, compression_config)
            elif compression_type == CompressionType.DISTILLATION:
                return self._distill_model(
                    model_copy,
                    teacher_model,
                    training_data,
                    compression_config
                )
            elif compression_type == CompressionType.STRUCTURE:
                return self._compress_structure(model_copy, compression_config)
            else:
                raise ValueError(f"不支持的压缩类型: {compression_type}")
                
        except Exception as e:
            logging.error(f"模型压缩失败: {str(e)}")
            raise
    
    def _prune_model(self,
                     model: nn.Module,
                     config: Dict[str, Any]) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        模型剪枝
        :param model: 模型实例
        :param config: 剪枝配置
        :return: (剪枝后的模型, 剪枝信息)
        """
        try:
            pruning_method = config.get('method', 'l1_unstructured')
            amount = config.get('amount', 0.3)
            
            # 记录原始参数数量
            original_params = sum(p.numel() for p in model.parameters())
            
            # 对每个线性层和卷积层进行剪枝
            for name, module in model.named_modules():
                if isinstance(module, (nn.Linear, nn.Conv2d)):
                    if pruning_method == 'l1_unstructured':
                        prune.l1_unstructured(
                            module,
                            name='weight',
                            amount=amount
                        )
                    elif pruning_method == 'random_unstructured':
                        prune.random_unstructured(
                            module,
                            name='weight',
                            amount=amount
                        )
                    # 应用剪枝掩码
                    prune.remove(module, 'weight')
            
            # 计算剪枝后的参数数量
            pruned_params = sum(p.numel() for p in model.parameters())
            
            # 收集剪枝信息
            info = {
                'compression_type': CompressionType.PRUNING,
                'method': pruning_method,
                'amount': amount,
                'original_params': original_params,
                'pruned_params': pruned_params,
                'compression_ratio': original_params / pruned_params,
                'timestamp': datetime.now().isoformat()
            }
            
            return model, info
            
        except Exception as e:
            logging.error(f"模型剪枝失败: {str(e)}")
            raise
    
    def _distill_model(self,
                      student_model: nn.Module,
                      teacher_model: nn.Module,
                      training_data: torch.utils.data.DataLoader,
                      config: Dict[str, Any]) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        知识蒸馏
        :param student_model: 学生模型
        :param teacher_model: 教师模型
        :param training_data: 训练数据
        :param config: 蒸馏配置
        :return: (蒸馏后的模型, 蒸馏信息)
        """
        try:
            temperature = config.get('temperature', 4.0)
            alpha = config.get('alpha', 0.5)
            epochs = config.get('epochs', 10)
            
            # 准备模型
            student_model.train()
            teacher_model.eval()
            
            # 配置优化器
            optimizer = torch.optim.Adam(
                student_model.parameters(),
                lr=config.get('learning_rate', 0.001)
            )
            
            # 记录蒸馏历史
            history = {
                'student_loss': [],
                'distillation_loss': [],
                'total_loss': []
            }
            
            # 蒸馏训练
            for epoch in range(epochs):
                epoch_losses = {k: 0.0 for k in history.keys()}
                
                for batch in training_data:
                    # 准备数据
                    inputs = {k: v.to(self.device) for k, v in batch.items()}
                    
                    # 教师模型预测
                    with torch.no_grad():
                        teacher_outputs = teacher_model(**inputs)
                    
                    # 学生模型预测
                    student_outputs = student_model(**inputs)
                    
                    # 计算损失
                    student_loss = self._calculate_student_loss(
                        student_outputs,
                        inputs
                    )
                    
                    distillation_loss = self._calculate_distillation_loss(
                        student_outputs,
                        teacher_outputs,
                        temperature
                    )
                    
                    # 总损失
                    total_loss = (
                        alpha * student_loss +
                        (1 - alpha) * distillation_loss
                    )
                    
                    # 反向传播
                    optimizer.zero_grad()
                    total_loss.backward()
                    optimizer.step()
                    
                    # 记录损失
                    epoch_losses['student_loss'] += student_loss.item()
                    epoch_losses['distillation_loss'] += distillation_loss.item()
                    epoch_losses['total_loss'] += total_loss.item()
                
                # 更新历史
                for k, v in epoch_losses.items():
                    history[k].append(v / len(training_data))
            
            # 收集蒸馏信息
            info = {
                'compression_type': CompressionType.DISTILLATION,
                'temperature': temperature,
                'alpha': alpha,
                'epochs': epochs,
                'history': history,
                'timestamp': datetime.now().isoformat()
            }
            
            return student_model, info
            
        except Exception as e:
            logging.error(f"知识蒸馏失败: {str(e)}")
            raise
    
    def _compress_structure(self,
                          model: nn.Module,
                          config: Dict[str, Any]) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        结构压缩
        :param model: 模型实例
        :param config: 压缩配置
        :return: (压缩后的模型, 压缩信息)
        """
        try:
            compression_ratio = config.get('compression_ratio', 0.5)
            
            # 记录原始结构信息
            original_structure = self._get_model_structure(model)
            
            # 压缩每个线性层
            for name, module in model.named_modules():
                if isinstance(module, nn.Linear):
                    in_features = module.in_features
                    out_features = module.out_features
                    
                    # 计算新的特征维度
                    new_features = int(min(in_features, out_features) * compression_ratio)
                    
                    # 创建新的压缩层
                    compressed_layer = nn.Linear(
                        in_features,
                        new_features,
                        bias=module.bias is not None
                    )
                    
                    # 使用SVD压缩权重
                    with torch.no_grad():
                        U, S, V = torch.svd(module.weight.data)
                        compressed_layer.weight.data = torch.mm(
                            U[:, :new_features],
                            torch.mm(
                                torch.diag(S[:new_features]),
                                V[:, :new_features].t()
                            )
                        )
                        if module.bias is not None:
                            compressed_layer.bias.data = module.bias.data
                    
                    # 替换原层
                    setattr(model, name, compressed_layer)
            
            # 获取压缩后的结构信息
            compressed_structure = self._get_model_structure(model)
            
            # 收集压缩信息
            info = {
                'compression_type': CompressionType.STRUCTURE,
                'compression_ratio': compression_ratio,
                'original_structure': original_structure,
                'compressed_structure': compressed_structure,
                'timestamp': datetime.now().isoformat()
            }
            
            return model, info
            
        except Exception as e:
            logging.error(f"结构压缩失败: {str(e)}")
            raise
    
    def _calculate_student_loss(self,
                              student_outputs: Dict[str, torch.Tensor],
                              targets: Dict[str, torch.Tensor]) -> torch.Tensor:
        """计算学生模型损失"""
        try:
            total_loss = torch.tensor(0.0).to(self.device)
            
            for key in student_outputs:
                if key in targets:
                    if student_outputs[key].shape[-1] > 1:
                        # 分类任务
                        loss_fn = nn.CrossEntropyLoss()
                        total_loss += loss_fn(
                            student_outputs[key],
                            targets[key]
                        )
                    else:
                        # 回归任务
                        loss_fn = nn.MSELoss()
                        total_loss += loss_fn(
                            student_outputs[key],
                            targets[key]
                        )
            
            return total_loss
            
        except Exception as e:
            logging.error(f"计算学生模型损失失败: {str(e)}")
            raise
    
    def _calculate_distillation_loss(self,
                                   student_outputs: Dict[str, torch.Tensor],
                                   teacher_outputs: Dict[str, torch.Tensor],
                                   temperature: float) -> torch.Tensor:
        """计算蒸馏损失"""
        try:
            total_loss = torch.tensor(0.0).to(self.device)
            
            for key in student_outputs:
                if key in teacher_outputs:
                    # 软目标蒸馏
                    student_logits = student_outputs[key] / temperature
                    teacher_logits = teacher_outputs[key] / temperature
                    
                    loss_fn = nn.KLDivLoss(reduction='batchmean')
                    total_loss += (
                        temperature * temperature *
                        loss_fn(
                            torch.log_softmax(student_logits, dim=-1),
                            torch.softmax(teacher_logits, dim=-1)
                        )
                    )
            
            return total_loss
            
        except Exception as e:
            logging.error(f"计算蒸馏损失失败: {str(e)}")
            raise
    
    def _get_model_structure(self, model: nn.Module) -> Dict[str, Any]:
        """获取模型结构信息"""
        structure = {}
        for name, module in model.named_modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                structure[name] = {
                    'type': module.__class__.__name__,
                    'parameters': sum(p.numel() for p in module.parameters())
                }
                if isinstance(module, nn.Linear):
                    structure[name].update({
                        'in_features': module.in_features,
                        'out_features': module.out_features
                    })
                elif isinstance(module, nn.Conv2d):
                    structure[name].update({
                        'in_channels': module.in_channels,
                        'out_channels': module.out_channels,
                        'kernel_size': module.kernel_size
                    })
        return structure
    
    def save_compressed_model(self,
                            model: nn.Module,
                            compression_info: Dict[str, Any],
                            user_id: int,
                            model_type: str) -> str:
        """
        保存压缩模型
        :param model: 压缩后的模型
        :param compression_info: 压缩信息
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 保存路径
        """
        try:
            # 创建保存目录
            save_path = self.compressed_dir / f"{model_type}_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 保存模型
            model_path = save_path / 'compressed_model.pt'
            torch.save(model.state_dict(), model_path)
            
            # 保存压缩信息
            info_path = save_path / 'compression_info.json'
            with open(info_path, 'w') as f:
                json.dump(compression_info, f, indent=2)
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"保存压缩模型失败: {str(e)}")
            raise 