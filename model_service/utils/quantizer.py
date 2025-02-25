import torch
import torch.quantization
from typing import Dict, Any, Optional, Union, Tuple
import logging
from pathlib import Path
import json
from datetime import datetime
import copy
import numpy as np

class ModelQuantizer:
    """模型量化器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.quantized_dir = Path(config.get('quantized_dir', 'quantized_models'))
        
        # 创建量化模型目录
        self.quantized_dir.mkdir(parents=True, exist_ok=True)
    
    def quantize_model(self,
                      model: torch.nn.Module,
                      calibration_data: Optional[torch.utils.data.DataLoader] = None,
                      quant_type: str = 'dynamic',
                      qconfig: Optional[Dict[str, Any]] = None) -> Tuple[torch.nn.Module, Dict[str, Any]]:
        """
        量化模型
        :param model: 原始模型
        :param calibration_data: 校准数据
        :param quant_type: 量化类型 ('dynamic', 'static', 'qat')
        :param qconfig: 量化配置
        :return: (量化后的模型, 量化信息)
        """
        try:
            # 准备模型副本
            model_copy = copy.deepcopy(model)
            model_copy.eval()
            
            # 选择量化方法
            if quant_type == 'dynamic':
                quantized_model = self._dynamic_quantize(model_copy, qconfig)
            elif quant_type == 'static':
                quantized_model = self._static_quantize(
                    model_copy,
                    calibration_data,
                    qconfig
                )
            elif quant_type == 'qat':
                quantized_model = self._quantization_aware_training(
                    model_copy,
                    calibration_data,
                    qconfig
                )
            else:
                raise ValueError(f"不支持的量化类型: {quant_type}")
            
            # 收集量化信息
            quant_info = self._collect_quantization_info(
                original_model=model,
                quantized_model=quantized_model,
                quant_type=quant_type,
                qconfig=qconfig
            )
            
            return quantized_model, quant_info
            
        except Exception as e:
            logging.error(f"模型量化失败: {str(e)}")
            raise
    
    def _dynamic_quantize(self,
                         model: torch.nn.Module,
                         qconfig: Optional[Dict[str, Any]] = None) -> torch.nn.Module:
        """动态量化"""
        try:
            # 设置默认量化配置
            if qconfig is None:
                qconfig = {
                    'dtype': torch.qint8,
                    'qscheme': torch.per_tensor_affine
                }
            
            # 应用动态量化
            quantized_model = torch.quantization.quantize_dynamic(
                model,
                qconfig_spec=qconfig,
                dtype=qconfig.get('dtype', torch.qint8)
            )
            
            return quantized_model
            
        except Exception as e:
            logging.error(f"动态量化失败: {str(e)}")
            raise
    
    def _static_quantize(self,
                        model: torch.nn.Module,
                        calibration_data: torch.utils.data.DataLoader,
                        qconfig: Optional[Dict[str, Any]] = None) -> torch.nn.Module:
        """静态量化"""
        try:
            # 设置默认量化配置
            if qconfig is None:
                qconfig = torch.quantization.get_default_qconfig('fbgemm')
            
            # 准备量化
            model.qconfig = qconfig
            torch.quantization.prepare(model, inplace=True)
            
            # 校准
            with torch.no_grad():
                for batch in calibration_data:
                    if isinstance(batch, dict):
                        model(**batch)
                    else:
                        model(batch)
            
            # 转换为量化模型
            quantized_model = torch.quantization.convert(model, inplace=False)
            
            return quantized_model
            
        except Exception as e:
            logging.error(f"静态量化失败: {str(e)}")
            raise
    
    def _quantization_aware_training(self,
                                   model: torch.nn.Module,
                                   calibration_data: torch.utils.data.DataLoader,
                                   qconfig: Optional[Dict[str, Any]] = None) -> torch.nn.Module:
        """量化感知训练"""
        try:
            # 设置默认量化配置
            if qconfig is None:
                qconfig = torch.quantization.get_default_qat_qconfig('fbgemm')
            
            # 准备QAT
            model.train()
            model.qconfig = qconfig
            torch.quantization.prepare_qat(model, inplace=True)
            
            # 执行QAT训练
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            num_epochs = self.config.get('qat_epochs', 5)
            
            for epoch in range(num_epochs):
                for batch in calibration_data:
                    optimizer.zero_grad()
                    if isinstance(batch, dict):
                        outputs = model(**batch)
                    else:
                        outputs = model(batch)
                    
                    # 计算损失
                    loss = self._calculate_qat_loss(outputs, batch)
                    loss.backward()
                    optimizer.step()
            
            # 转换为量化模型
            model.eval()
            quantized_model = torch.quantization.convert(model, inplace=False)
            
            return quantized_model
            
        except Exception as e:
            logging.error(f"量化感知训练失败: {str(e)}")
            raise
    
    def _calculate_qat_loss(self,
                           outputs: Union[torch.Tensor, Dict[str, torch.Tensor]],
                           batch: Union[torch.Tensor, Dict[str, torch.Tensor]]) -> torch.Tensor:
        """计算QAT损失"""
        try:
            if isinstance(outputs, dict) and isinstance(batch, dict):
                # 多任务损失
                total_loss = torch.tensor(0.0).to(self.device)
                for key in outputs:
                    if key in batch:
                        loss_fn = torch.nn.MSELoss()
                        total_loss += loss_fn(outputs[key], batch[key])
                return total_loss
            else:
                # 单任务损失
                loss_fn = torch.nn.MSELoss()
                return loss_fn(outputs, batch)
            
        except Exception as e:
            logging.error(f"计算QAT损失失败: {str(e)}")
            raise
    
    def _collect_quantization_info(self,
                                 original_model: torch.nn.Module,
                                 quantized_model: torch.nn.Module,
                                 quant_type: str,
                                 qconfig: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """收集量化信息"""
        try:
            # 计算模型大小
            orig_size = self._get_model_size(original_model)
            quant_size = self._get_model_size(quantized_model)
            
            # 收集信息
            info = {
                'quantization_type': quant_type,
                'original_size_mb': orig_size,
                'quantized_size_mb': quant_size,
                'compression_ratio': orig_size / quant_size if quant_size > 0 else 0,
                'qconfig': qconfig,
                'timestamp': datetime.now().isoformat()
            }
            
            return info
            
        except Exception as e:
            logging.error(f"收集量化信息失败: {str(e)}")
            raise
    
    def _get_model_size(self, model: torch.nn.Module) -> float:
        """获取模型大小(MB)"""
        param_size = 0
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        buffer_size = 0
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        size_mb = (param_size + buffer_size) / 1024 / 1024
        return size_mb
    
    def save_quantized_model(self,
                           model: torch.nn.Module,
                           quant_info: Dict[str, Any],
                           user_id: int,
                           model_type: str) -> str:
        """
        保存量化模型
        :param model: 量化后的模型
        :param quant_info: 量化信息
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 保存路径
        """
        try:
            # 创建保存目录
            save_path = self.quantized_dir / f"{model_type}_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 保存模型
            model_path = save_path / 'quantized_model.pt'
            torch.save(model.state_dict(), model_path)
            
            # 保存量化信息
            info_path = save_path / 'quantization_info.json'
            with open(info_path, 'w') as f:
                json.dump(quant_info, f, indent=2)
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"保存量化模型失败: {str(e)}")
            raise 