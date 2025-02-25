import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging
from pathlib import Path
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class TrainingVisualizer:
    """训练过程可视化器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.viz_dir = Path(config.get('visualization_dir', 'visualizations'))
        
        # 创建可视化目录
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置样式
        plt.style.use('seaborn')
        sns.set_palette("husl")
    
    def plot_training_history(self,
                            history: Dict[str, Any],
                            user_id: int,
                            model_type: str) -> str:
        """
        绘制训练历史
        :param history: 训练历史数据
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 图表保存路径
        """
        try:
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Loss Curve',
                    'Learning Rate',
                    'Metrics',
                    'Training Progress'
                )
            )
            
            # 绘制损失曲线
            epochs = list(range(len(history['loss'])))
            fig.add_trace(
                go.Scatter(x=epochs, y=history['loss'],
                          name='Training Loss',
                          line=dict(color='blue')),
                row=1, col=1
            )
            if 'val_loss' in history:
                fig.add_trace(
                    go.Scatter(x=epochs, y=history['val_loss'],
                              name='Validation Loss',
                              line=dict(color='red')),
                    row=1, col=1
                )
            
            # 绘制学习率变化
            if 'learning_rate' in history:
                fig.add_trace(
                    go.Scatter(x=epochs, y=history['learning_rate'],
                              name='Learning Rate',
                              line=dict(color='green')),
                    row=1, col=2
                )
            
            # 绘制评估指标
            if 'metrics' in history:
                for metric_name, values in history['metrics'].items():
                    fig.add_trace(
                        go.Scatter(x=epochs, y=values,
                                  name=metric_name),
                        row=2, col=1
                    )
            
            # 绘制训练进度
            if 'progress' in history:
                fig.add_trace(
                    go.Indicator(
                        mode="gauge+number",
                        value=history['progress'][-1],
                        title={'text': "Training Progress"},
                        gauge={'axis': {'range': [0, 100]}},
                    ),
                    row=2, col=2
                )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text=f"{model_type.capitalize()} Model Training History",
                showlegend=True
            )
            
            # 保存图表
            save_path = self.viz_dir / f"{model_type}_{user_id}_training_history.html"
            fig.write_html(str(save_path))
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"绘制训练历史失败: {str(e)}")
            raise
    
    def plot_model_performance(self,
                             metrics: Dict[str, Any],
                             user_id: int,
                             model_type: str) -> str:
        """
        绘制模型性能指标
        :param metrics: 性能指标
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 图表保存路径
        """
        try:
            # 创建性能仪表板
            fig = make_subplots(
                rows=2, cols=2,
                specs=[[{'type': 'domain'}, {'type': 'domain'}],
                      [{'colspan': 2}, None]],
                subplot_titles=(
                    'Accuracy Metrics',
                    'Loss Metrics',
                    'Performance Comparison'
                )
            )
            
            # 添加准确率指标
            accuracy_metrics = {k: v for k, v in metrics.items() if 'accuracy' in k}
            fig.add_trace(
                go.Pie(labels=list(accuracy_metrics.keys()),
                      values=list(accuracy_metrics.values()),
                      name="Accuracy Metrics"),
                row=1, col=1
            )
            
            # 添加损失指标
            loss_metrics = {k: v for k, v in metrics.items() if 'loss' in k}
            fig.add_trace(
                go.Pie(labels=list(loss_metrics.keys()),
                      values=list(loss_metrics.values()),
                      name="Loss Metrics"),
                row=1, col=2
            )
            
            # 添加性能对比条形图
            fig.add_trace(
                go.Bar(x=list(metrics.keys()),
                      y=list(metrics.values()),
                      name="Performance Metrics"),
                row=2, col=1
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text=f"{model_type.capitalize()} Model Performance",
                showlegend=True
            )
            
            # 保存图表
            save_path = self.viz_dir / f"{model_type}_{user_id}_performance.html"
            fig.write_html(str(save_path))
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"绘制模型性能失败: {str(e)}")
            raise
    
    def plot_predictions(self,
                        predictions: Dict[str, Any],
                        user_id: int,
                        model_type: str) -> str:
        """
        绘制预测结果
        :param predictions: 预测结果
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 图表保存路径
        """
        try:
            if model_type == 'student':
                return self._plot_student_predictions(predictions, user_id)
            else:
                return self._plot_teacher_predictions(predictions, user_id)
            
        except Exception as e:
            logging.error(f"绘制预测结果失败: {str(e)}")
            raise
    
    def _plot_student_predictions(self,
                                predictions: Dict[str, Any],
                                user_id: int) -> str:
        """绘制学生模型预测结果"""
        try:
            # 创建预测结果可视化
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Weaknesses Distribution',
                    'Interests Distribution',
                    'Learning Path',
                    'Prediction Confidence'
                )
            )
            
            # 绘制薄弱点分布
            weaknesses = predictions['weaknesses']
            fig.add_trace(
                go.Bar(x=[w['label'] for w in weaknesses],
                      y=[w['probability'] for w in weaknesses],
                      name="Weaknesses"),
                row=1, col=1
            )
            
            # 绘制兴趣点分布
            interests = predictions['interests']
            fig.add_trace(
                go.Bar(x=[i['label'] for i in interests],
                      y=[i['probability'] for i in interests],
                      name="Interests"),
                row=1, col=2
            )
            
            # 绘制学习路径
            path = predictions['learning_path']
            fig.add_trace(
                go.Scatter(x=[p['step'] for p in path],
                          y=[p['probability'] for p in path],
                          mode='lines+markers',
                          name="Learning Path"),
                row=2, col=1
            )
            
            # 绘制预测置信度
            all_probs = (
                [w['probability'] for w in weaknesses] +
                [i['probability'] for i in interests] +
                [p['probability'] for p in path]
            )
            fig.add_trace(
                go.Box(y=all_probs,
                      name="Prediction Confidence"),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text="Student Model Predictions",
                showlegend=True
            )
            
            # 保存图表
            save_path = self.viz_dir / f"student_{user_id}_predictions.html"
            fig.write_html(str(save_path))
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"绘制学生预测结果失败: {str(e)}")
            raise
    
    def _plot_teacher_predictions(self,
                                predictions: Dict[str, Any],
                                user_id: int) -> str:
        """绘制教师模型预测结果"""
        try:
            # 创建预测结果可视化
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Content Coverage',
                    'Student Layer Distribution',
                    'Teaching Suggestions',
                    'Overall Analysis'
                )
            )
            
            # 绘制内容覆盖率
            coverage = predictions['coverage']
            fig.add_trace(
                go.Bar(x=list(coverage.keys()),
                      y=list(coverage.values()),
                      name="Content Coverage"),
                row=1, col=1
            )
            
            # 绘制学生分层分布
            layers = predictions['student_layers']
            fig.add_trace(
                go.Pie(labels=list(layers.keys()),
                      values=list(layers.values()),
                      name="Student Layers"),
                row=1, col=2
            )
            
            # 显示教学建议
            suggestions = predictions['suggestions']
            fig.add_trace(
                go.Table(
                    header=dict(values=['Teaching Suggestions']),
                    cells=dict(values=[suggestions])
                ),
                row=2, col=1
            )
            
            # 绘制总体分析
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=np.mean(list(coverage.values())) * 100,
                    title={'text': "Overall Coverage"},
                    gauge={'axis': {'range': [0, 100]}},
                ),
                row=2, col=2
            )
            
            # 更新布局
            fig.update_layout(
                height=800,
                title_text="Teacher Model Predictions",
                showlegend=True
            )
            
            # 保存图表
            save_path = self.viz_dir / f"teacher_{user_id}_predictions.html"
            fig.write_html(str(save_path))
            
            return str(save_path)
            
        except Exception as e:
            logging.error(f"绘制教师预测结果失败: {str(e)}")
            raise 