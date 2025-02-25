import torch
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import json
from pathlib import Path
import asyncio
from .llm_client import LLMClientFactory
import numpy as np
from torch.utils.data import DataLoader
from .data_loader import DataLoaderFactory
from .evaluator import ModelEvaluator
from .model_manager import ModelManager
from .early_stopping import EarlyStopping, EarlyStoppingMode
from .lr_scheduler import LRSchedulerFactory, SchedulerType, LRMonitor
from .quantizer import ModelQuantizer
from .model_ensemble import ModelEnsemble, EnsembleType
from .visualizer import TrainingVisualizer
from .distributed_trainer import DistributedTrainer
from .model_compressor import ModelCompressor, CompressionType
from ..monitoring.metrics import MetricsCollector
from .cache import CacheManager, CACHE_KEYS

class TrainingManager:
    """训练任务管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_dir = config['model_dir']
        self.max_epochs = config.get('max_epochs', 100)
        self.batch_size = config.get('batch_size', 32)
        self.learning_rate = config.get('learning_rate', 0.001)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.training_status = {}
        
        # 创建模型目录
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化评估器
        self.evaluator = ModelEvaluator(config)
        
        # 初始化模型管理器
        self.model_manager = ModelManager(config)
        
        # 初始化早停器
        early_stopping_config = {
            'patience': config.get('patience', 5),
            'min_delta': config.get('min_delta', 1e-4),
            'baseline': config.get('loss_baseline', None),
            'restore_best': True
        }
        self.early_stopping = EarlyStopping(
            early_stopping_config,
            mode=EarlyStoppingMode.MIN
        )
        
        # 初始化学习率监控器
        self.lr_monitor = LRMonitor(config)
        
        # 初始化量化器
        self.quantizer = ModelQuantizer(config)
        
        # 初始化模型集成器
        self.model_ensemble = ModelEnsemble(config)
        
        # 初始化可视化器
        self.visualizer = TrainingVisualizer(config)
        
        # 初始化分布式训练器
        self.distributed_trainer = DistributedTrainer(config)
        
        # 初始化模型压缩器
        self.model_compressor = ModelCompressor(config)
        
        # 初始化缓存管理器
        self.cache_manager = CacheManager(config)
    
    async def train_student_model(self,
                                model: torch.nn.Module,
                                student_id: int,
                                training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        训练学生模型
        :param model: 模型实例
        :param student_id: 学生ID
        :param training_data: 训练数据
        :return: 训练结果
        """
        try:
            # 更新训练状态
            self.training_status[student_id] = {
                'status': 'training',
                'start_time': datetime.now().isoformat(),
                'progress': 0
            }
            
            # 预处理数据
            processed_data = await self._preprocess_student_data(training_data)
            
            # 准备数据加载器
            train_loader = self._prepare_data_loader(processed_data)
            
            # 创建优化器
            optimizer = torch.optim.Adam(
                model.parameters(),
                lr=self.learning_rate
            )
            
            # 创建学习率调度器
            scheduler = LRSchedulerFactory.create_scheduler(
                optimizer,
                SchedulerType(self.config.get('scheduler_type', 'warmup')),
                {
                    'warmup_epochs': 5,
                    'total_epochs': self.max_epochs,
                    'base_scheduler': SchedulerType.COSINE
                }
            )
            
            # 移动模型到设备
            model = model.to(self.device)
            
            # 训练循环
            best_loss = float('inf')
            patience = self.config.get('patience', 5)
            patience_counter = 0
            
            for epoch in range(self.max_epochs):
                model.train()
                total_loss = 0
                
                for batch in train_loader:
                    # 移动数据到设备
                    text_features = batch['text'].to(self.device)
                    sequence_features = batch['sequence'].to(self.device)
                    labels = {
                        'weaknesses': batch['weaknesses'].to(self.device),
                        'interests': batch['interests'].to(self.device),
                        'path': batch['path'].to(self.device)
                    }
                    
                    # 前向传播
                    optimizer.zero_grad()
                    outputs = model(text_features, sequence_features)
                    
                    # 计算损失
                    loss = self._calculate_loss(outputs, labels)
                    
                    # 反向传播
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                # 计算平均损失
                avg_loss = total_loss / len(train_loader)
                
                # 评估模型
                if epoch % self.config.get('eval_interval', 5) == 0:
                    eval_metrics = self.evaluator.evaluate_student_model(
                        model,
                        eval_loader,
                        student_id
                    )
                    logging.info(f"Epoch {epoch} evaluation: {eval_metrics}")
                    
                    # 更新训练状态
                    self.training_status[student_id]['metrics'] = eval_metrics
                    
                    # 添加验证指标
                    self.early_stopping.add_validation_metrics(eval_metrics)
                
                # 检查早停
                should_stop = self.early_stopping(
                    epoch,
                    avg_loss,
                    model.state_dict(),
                    eval_metrics if epoch % self.config.get('eval_interval', 5) == 0 else None
                )
                
                if should_stop:
                    logging.info("Early stopping triggered")
                    break
                
                # 更新进度
                progress = (epoch + 1) / self.max_epochs * 100
                self.training_status[student_id]['progress'] = progress
                
                # 更新学习率
                current_lr = scheduler.get_lr()[0]
                scheduler.step()
                
                # 记录学习率
                self.lr_monitor.step(
                    epoch,
                    current_lr,
                    eval_metrics if epoch % self.config.get('eval_interval', 5) == 0 else None
                )
                
                # 更新训练状态
                self.training_status[student_id]['current_lr'] = current_lr
                
                # 更新训练指标
                MetricsCollector.update_training_metrics(
                    user_id=student_id,
                    model_type='student',
                    status=1,  # training
                    progress=progress,
                    loss=avg_loss
                )
            
            # 如果需要恢复最佳模型
            best_state = self.early_stopping.get_best_state()
            if best_state is not None:
                model.load_state_dict(best_state)
            
            # 添加训练总结到状态
            self.training_status[student_id]['training_summary'] = \
                self.early_stopping.get_training_summary()
            
            # 训练完成
            self.training_status[student_id].update({
                'status': 'completed',
                'end_time': datetime.now().isoformat(),
                'final_loss': avg_loss
            })
            
            # 保存学习率历史
            self.lr_monitor.save_history(student_id, 'student')
            
            # 生成训练可视化
            viz_path = self.visualizer.plot_training_history(
                {
                    'loss': training_history['loss'],
                    'val_loss': training_history.get('val_loss', []),
                    'learning_rate': self.lr_monitor.history,
                    'metrics': training_history.get('metrics', {}),
                    'progress': training_history['progress']
                },
                student_id,
                'student'
            )
            
            # 生成性能可视化
            perf_path = self.visualizer.plot_model_performance(
                self.training_status[student_id]['metrics'],
                student_id,
                'student'
            )
            
            # 更新训练状态
            self.training_status[student_id]['visualizations'] = {
                'training_history': viz_path,
                'performance': perf_path
            }
            
            # 更新完成状态
            MetricsCollector.update_training_metrics(
                user_id=student_id,
                model_type='student',
                status=2,  # completed
                progress=100.0,
                loss=avg_loss
            )
            
            # 使训练状态缓存失效
            self.cache_manager.invalidate(
                CACHE_KEYS['training_status'],
                student_id
            )
            
            # 训练完成后使相关缓存失效
            self.cache_manager.invalidate(
                CACHE_KEYS['model_info'],
                student_id,
                'student'
            )
            
            return {
                'status': 'success',
                'model_path': f"{self.model_dir}/student_{student_id}",
                'training_info': self.training_status[student_id]
            }
            
        except Exception as e:
            # 更新失败状态
            MetricsCollector.update_training_metrics(
                user_id=student_id,
                model_type='student',
                status=3,  # failed
                progress=progress
            )
            logging.error(f"学生模型训练失败: {str(e)}")
            self.training_status[student_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            raise
    
    async def train_teacher_model(self,
                                model: torch.nn.Module,
                                teacher_id: int,
                                training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        训练教师模型
        :param model: 模型实例
        :param teacher_id: 教师ID
        :param training_data: 训练数据
        :return: 训练结果
        """
        try:
            # 更新训练状态
            self.training_status[teacher_id] = {
                'status': 'training',
                'start_time': datetime.now().isoformat(),
                'progress': 0
            }
            
            # 预处理数据
            processed_data = await self._preprocess_teacher_data(training_data)
            
            # 准备数据加载器
            train_loader = self._prepare_data_loader(processed_data)
            
            # 配置优化器
            optimizer = torch.optim.Adam(
                model.parameters(),
                lr=self.learning_rate
            )
            
            # 移动模型到设备
            model = model.to(self.device)
            
            # 训练循环
            best_loss = float('inf')
            patience = self.config.get('patience', 5)
            patience_counter = 0
            
            for epoch in range(self.max_epochs):
                model.train()
                total_loss = 0
                
                for batch in train_loader:
                    # 移动数据到设备
                    content_features = batch['content'].to(self.device)
                    student_features = batch['student_data'].to(self.device)
                    
                    # 前向传播
                    optimizer.zero_grad()
                    outputs = model(content_features, student_features)
                    
                    # 计算损失
                    loss = self._calculate_teacher_loss(outputs, batch)
                    
                    # 反向传播
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                # 计算平均损失
                avg_loss = total_loss / len(train_loader)
                
                # 早停检查
                if avg_loss < best_loss:
                    best_loss = avg_loss
                    patience_counter = 0
                    # 保存最佳模型
                    self._save_model(model, teacher_id, epoch, avg_loss)
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logging.info(f"Early stopping at epoch {epoch}")
                        break
                
                # 更新进度
                progress = (epoch + 1) / self.max_epochs * 100
                self.training_status[teacher_id]['progress'] = progress
                
                # 在每个epoch结束后评估
                if epoch % self.config.get('eval_interval', 5) == 0:
                    eval_metrics = self.evaluator.evaluate_teacher_model(
                        model,
                        eval_loader,  # 需要添加验证数据加载器
                        teacher_id
                    )
                    logging.info(f"Epoch {epoch} evaluation: {eval_metrics}")
                    
                    # 更新训练状态
                    self.training_status[teacher_id]['metrics'] = eval_metrics
            
            # 训练完成
            self.training_status[teacher_id].update({
                'status': 'completed',
                'end_time': datetime.now().isoformat(),
                'final_loss': best_loss
            })
            
            return {
                'status': 'success',
                'model_path': f"{self.model_dir}/teacher_{teacher_id}",
                'training_info': self.training_status[teacher_id]
            }
            
        except Exception as e:
            logging.error(f"教师模型训练失败: {str(e)}")
            self.training_status[teacher_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            raise
    
    def get_training_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取训练状态"""
        return self.training_status.get(user_id)
    
    def _save_model(self,
                   model: torch.nn.Module,
                   user_id: int,
                   epoch: int,
                   loss: float):
        """保存模型"""
        try:
            # 准备模型信息
            model_info = {
                'epoch': epoch,
                'loss': loss,
                'metrics': self.training_status[user_id].get('metrics', {}),
                'training_status': self.training_status[user_id]
            }
            
            # 确定模型类型
            model_type = 'student' if isinstance(model, StudentModel) else 'teacher'
            
            # 保存模型
            version_id = self.model_manager.save_model(
                model,
                model_info,
                user_id,
                model_type
            )
            
            # 更新训练状态
            self.training_status[user_id]['model_version'] = version_id
            
            # 使模型信息缓存失效
            self.cache_manager.invalidate(
                CACHE_KEYS['model_info'],
                user_id,
                model_type
            )
            
        except Exception as e:
            logging.error(f"保存模型失败: {str(e)}")
            raise
    
    async def _preprocess_student_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理学生数据"""
        try:
            # 创建LLM客户端用于文本处理
            llm_config = {
                'api_key': os.getenv('XAI_API_KEY'),
                'base_url': 'https://api.xai.com/v1'
            }
            llm_client = LLMClientFactory.create_client('xai', llm_config)
            
            # 处理文本数据
            text_embeddings = await llm_client.embed(data['text'])
            
            # 处理序列数据
            sequence_features = torch.tensor(data['sequence'], dtype=torch.float32)
            
            # 处理标签
            labels = {
                'weaknesses': torch.tensor(data['labels']['weaknesses'], dtype=torch.float32),
                'interests': torch.tensor(data['labels']['interests'], dtype=torch.float32),
                'path': torch.tensor(data['labels']['path'], dtype=torch.float32)
            }
            
            await llm_client.close()
            
            return {
                'text': torch.tensor(text_embeddings, dtype=torch.float32),
                'sequence': sequence_features,
                **labels
            }
            
        except Exception as e:
            logging.error(f"预处理学生数据失败: {str(e)}")
            raise
    
    async def _preprocess_teacher_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理教师数据"""
        try:
            # 创建LLM客户端
            llm_config = {
                'api_key': os.getenv('XAI_API_KEY'),
                'base_url': 'https://api.xai.com/v1'
            }
            llm_client = LLMClientFactory.create_client('xai', llm_config)
            
            # 处理教学内容
            content_text = '\n'.join([
                *data['content']['plans'],
                *data['content']['recordings'],
                *data['content']['feedback']
            ])
            content_embeddings = await llm_client.embed(content_text)
            
            # 处理学生数据
            student_features = []
            for student in data['student_data']:
                # 提取学生特征
                features = [
                    student.get('average_score', 0),
                    student.get('attendance_rate', 0),
                    student.get('participation_rate', 0),
                    student.get('homework_completion_rate', 0)
                ]
                student_features.append(features)
            
            # 处理标签
            labels = {
                'coverage': torch.tensor(
                    [data['labels']['coverage'].get(subject, 0) 
                     for subject in self.config['subjects']],
                    dtype=torch.float32
                ),
                'student_layers': torch.tensor(
                    data['labels']['student_layers'],
                    dtype=torch.float32
                )
            }
            
            await llm_client.close()
            
            return {
                'content': torch.tensor(content_embeddings, dtype=torch.float32),
                'student_data': torch.tensor(student_features, dtype=torch.float32),
                **labels
            }
            
        except Exception as e:
            logging.error(f"预处理教师数据失败: {str(e)}")
            raise
    
    def _prepare_data_loader(self, data: Dict[str, Any]) -> DataLoader:
        """准备数据加载器"""
        try:
            # 确定模型类型
            model_type = 'student' if isinstance(self.model, StudentModel) else 'teacher'
            
            # 创建数据加载器
            loader = DataLoaderFactory.create_data_loader(
                data=data,
                config=self.config,
                model_type=model_type,
                batch_size=self.batch_size,
                shuffle=True
            )
            
            return loader
            
        except Exception as e:
            logging.error(f"准备数据加载器失败: {str(e)}")
            raise
    
    def _calculate_loss(self,
                       outputs: Dict[str, torch.Tensor],
                       labels: Dict[str, torch.Tensor]) -> torch.Tensor:
        """计算学生模型损失"""
        try:
            # 二元交叉熵损失(用于薄弱点和兴趣点)
            bce_loss = torch.nn.BCELoss()
            weakness_loss = bce_loss(outputs['weaknesses'], labels['weaknesses'])
            interest_loss = bce_loss(outputs['interests'], labels['interests'])
            
            # 交叉熵损失(用于学习路径)
            ce_loss = torch.nn.CrossEntropyLoss()
            path_loss = ce_loss(outputs['path'], labels['path'])
            
            # 组合损失
            total_loss = (
                self.config.get('weakness_weight', 0.4) * weakness_loss +
                self.config.get('interest_weight', 0.3) * interest_loss +
                self.config.get('path_weight', 0.3) * path_loss
            )
            
            return total_loss
            
        except Exception as e:
            logging.error(f"计算学生模型损失失败: {str(e)}")
            raise
    
    def _calculate_teacher_loss(self,
                              outputs: Dict[str, torch.Tensor],
                              batch: Dict[str, torch.Tensor]) -> torch.Tensor:
        """计算教师模型损失"""
        try:
            # KL散度损失(用于内容覆盖率)
            kl_loss = torch.nn.KLDivLoss(reduction='batchmean')
            coverage_loss = kl_loss(
                torch.log_softmax(outputs['coverage'], dim=-1),
                batch['coverage']
            )
            
            # 交叉熵损失(用于学生分层)
            ce_loss = torch.nn.CrossEntropyLoss()
            layer_loss = ce_loss(outputs['layers'], batch['student_layers'])
            
            # 组合损失
            total_loss = (
                self.config.get('coverage_weight', 0.5) * coverage_loss +
                self.config.get('layer_weight', 0.5) * layer_loss
            )
            
            return total_loss
            
        except Exception as e:
            logging.error(f"计算教师模型损失失败: {str(e)}")
            raise
    
    def _postprocess_student_predictions(self,
                                       outputs: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """后处理学生模型预测结果"""
        try:
            # 获取标签映射
            weakness_labels = self.config['weakness_labels']
            interest_labels = self.config['interest_labels']
            path_steps = self.config['path_steps']
            
            # 处理薄弱点预测
            weakness_probs = torch.sigmoid(outputs['weaknesses']).cpu().numpy()
            weaknesses = [
                {'label': label, 'probability': float(prob)}
                for label, prob in zip(weakness_labels, weakness_probs)
                if prob > self.config.get('weakness_threshold', 0.5)
            ]
            
            # 处理兴趣点预测
            interest_probs = torch.sigmoid(outputs['interests']).cpu().numpy()
            interests = [
                {'label': label, 'probability': float(prob)}
                for label, prob in zip(interest_labels, interest_probs)
                if prob > self.config.get('interest_threshold', 0.5)
            ]
            
            # 处理学习路径预测
            path_probs = torch.softmax(outputs['path'], dim=-1).cpu().numpy()
            learning_path = [
                {'step': step, 'probability': float(prob)}
                for step, prob in zip(path_steps, path_probs)
            ]
            
            return {
                'weaknesses': weaknesses,
                'interests': interests,
                'learning_path': learning_path
            }
            
        except Exception as e:
            logging.error(f"后处理学生模型预测失败: {str(e)}")
            raise
    
    def _postprocess_teacher_predictions(self,
                                       outputs: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """后处理教师模型预测结果"""
        try:
            # 获取标签映射
            subjects = self.config['subjects']
            layer_labels = self.config['layer_labels']
            
            # 处理覆盖率预测
            coverage_probs = torch.softmax(outputs['coverage'], dim=-1).cpu().numpy()
            coverage = {
                subject: float(prob)
                for subject, prob in zip(subjects, coverage_probs)
            }
            
            # 处理学生分层预测
            layer_probs = torch.softmax(outputs['layers'], dim=-1).cpu().numpy()
            student_layers = {
                label: int(count)
                for label, count in zip(layer_labels, layer_probs)
            }
            
            # 生成教学建议
            suggestions = self._generate_teaching_suggestions(coverage, student_layers)
            
            return {
                'coverage': coverage,
                'student_layers': student_layers,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logging.error(f"后处理教师模型预测失败: {str(e)}")
            raise
    
    def _generate_teaching_suggestions(self,
                                     coverage: Dict[str, float],
                                     layers: Dict[str, int]) -> List[str]:
        """生成教学建议"""
        suggestions = []
        
        # 基于覆盖率的建议
        low_coverage = [
            subject for subject, prob in coverage.items()
            if prob < self.config.get('coverage_threshold', 0.3)
        ]
        if low_coverage:
            suggestions.append(
                f"建议增加以下主题的教学内容: {', '.join(low_coverage)}"
            )
        
        # 基于学生分层的建议
        if layers.get('需要关注', 0) > layers.get('优秀', 0):
            suggestions.append(
                "建议加强个性化辅导，关注学习困难学生"
            )
        
        # 添加其他建议...
        
        return suggestions
    
    def quantize_trained_model(self,
                             model: torch.nn.Module,
                             user_id: int,
                             quant_type: str = 'dynamic',
                             calibration_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        量化训练好的模型
        :param model: 模型实例
        :param user_id: 用户ID
        :param quant_type: 量化类型
        :param calibration_data: 校准数据
        :return: 量化结果
        """
        try:
            # 准备校准数据加载器
            calibration_loader = None
            if calibration_data is not None:
                calibration_loader = self._prepare_data_loader(calibration_data)
            
            # 确定模型类型
            model_type = 'student' if isinstance(model, StudentModel) else 'teacher'
            
            # 量化模型
            quantized_model, quant_info = self.quantizer.quantize_model(
                model,
                calibration_loader,
                quant_type
            )
            
            # 保存量化模型
            save_path = self.quantizer.save_quantized_model(
                quantized_model,
                quant_info,
                user_id,
                model_type
            )
            
            return {
                'model_path': save_path,
                'quantization_info': quant_info
            }
            
        except Exception as e:
            logging.error(f"量化模型失败: {str(e)}")
            raise
    
    def create_model_ensemble(self,
                            models: List[torch.nn.Module],
                            weights: Optional[List[float]] = None,
                            user_id: int) -> Dict[str, Any]:
        """
        创建模型集成
        :param models: 模型列表
        :param weights: 权重列表
        :param user_id: 用户ID
        :return: 集成结果
        """
        try:
            # 确定模型类型
            model_type = 'student' if isinstance(models[0], StudentModel) else 'teacher'
            
            # 添加模型到集成
            for i, model in enumerate(models):
                weight = weights[i] if weights else 1.0
                self.model_ensemble.add_model(model, weight)
            
            # 保存集成模型
            ensemble_info = {
                'num_models': len(models),
                'model_type': model_type,
                'user_id': user_id
            }
            
            save_path = self.model_ensemble.save_ensemble(
                ensemble_info,
                user_id,
                model_type
            )
            
            return {
                'ensemble_path': save_path,
                'ensemble_info': ensemble_info
            }
            
        except Exception as e:
            logging.error(f"创建模型集成失败: {str(e)}")
            raise
    
    def ensemble_predict(self,
                        inputs: Dict[str, torch.Tensor],
                        ensemble_type: str = EnsembleType.WEIGHTED) -> Dict[str, Any]:
        """
        使用集成模型进行预测
        :param inputs: 输入数据
        :param ensemble_type: 集成类型
        :return: 预测结果
        """
        try:
            predictions = self.model_ensemble.predict(inputs, ensemble_type)
            
            # 后处理预测结果
            if isinstance(self.model_ensemble.models[0], StudentModel):
                return self._postprocess_student_predictions(predictions)
            else:
                return self._postprocess_teacher_predictions(predictions)
            
        except Exception as e:
            logging.error(f"集成预测失败: {str(e)}")
            raise
    
    def predict(self,
                predictions: Dict[str, Any],
                user_id: int,
                model_type: str) -> Dict[str, Any]:
        """
        生成预测可视化
        :param predictions: 预测结果
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 可视化结果
        """
        try:
            # 生成预测可视化
            viz_path = self.visualizer.plot_predictions(
                predictions,
                user_id,
                model_type
            )
            
            return {
                'predictions': predictions,
                'visualization': viz_path
            }
            
        except Exception as e:
            logging.error(f"生成预测可视化失败: {str(e)}")
            raise
    
    async def train_distributed(self,
                              model: torch.nn.Module,
                              user_id: int,
                              training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分布式训练
        :param model: 模型实例
        :param user_id: 用户ID
        :param training_data: 训练数据
        :return: 训练结果
        """
        try:
            # 确定训练函数
            train_fn = (
                self.train_student_model if isinstance(model, StudentModel)
                else self.train_teacher_model
            )
            
            # 执行分布式训练
            results = self.distributed_trainer.train(
                model,
                train_fn,
                user_id,
                training_data
            )
            
            # 更新训练状态
            self.training_status[user_id].update({
                'distributed_training': True,
                'world_size': self.distributed_trainer.world_size,
                'merged_results': results
            })
            
            return results
            
        except Exception as e:
            logging.error(f"分布式训练失败: {str(e)}")
            raise
    
    def compress_model(self,
                      model: torch.nn.Module,
                      user_id: int,
                      compression_type: str = CompressionType.PRUNING,
                      compression_config: Optional[Dict[str, Any]] = None,
                      training_data: Optional[Dict[str, Any]] = None,
                      teacher_model: Optional[torch.nn.Module] = None) -> Dict[str, Any]:
        """
        压缩模型
        :param model: 模型实例
        :param user_id: 用户ID
        :param compression_type: 压缩类型
        :param compression_config: 压缩配置
        :param training_data: 训练数据
        :param teacher_model: 教师模型
        :return: 压缩结果
        """
        try:
            # 准备数据加载器
            data_loader = None
            if training_data is not None:
                data_loader = self._prepare_data_loader(training_data)
            
            # 确定模型类型
            model_type = 'student' if isinstance(model, StudentModel) else 'teacher'
            
            # 压缩模型
            compressed_model, compression_info = self.model_compressor.compress_model(
                model,
                compression_type,
                compression_config or {},
                data_loader,
                teacher_model
            )
            
            # 保存压缩模型
            save_path = self.model_compressor.save_compressed_model(
                compressed_model,
                compression_info,
                user_id,
                model_type
            )
            
            return {
                'model_path': save_path,
                'compression_info': compression_info
            }
            
        except Exception as e:
            logging.error(f"压缩模型失败: {str(e)}")
            raise 