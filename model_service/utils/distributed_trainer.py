import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from typing import Dict, List, Any, Optional, Callable
import logging
from pathlib import Path
import os
import json
from datetime import datetime
from copy import deepcopy

class DistributedTrainer:
    """分布式训练器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.world_size = config.get('world_size', torch.cuda.device_count())
        self.backend = config.get('backend', 'nccl')
        self.dist_url = config.get('dist_url', 'tcp://127.0.0.1:23456')
        self.distributed_dir = Path(config.get('distributed_dir', 'distributed_models'))
        
        # 创建分布式训练目录
        self.distributed_dir.mkdir(parents=True, exist_ok=True)
    
    def setup(self, rank: int):
        """
        设置分布式环境
        :param rank: 进程编号
        """
        try:
            os.environ['MASTER_ADDR'] = '127.0.0.1'
            os.environ['MASTER_PORT'] = '23456'
            
            # 初始化进程组
            dist.init_process_group(
                backend=self.backend,
                init_method=self.dist_url,
                world_size=self.world_size,
                rank=rank
            )
            
            # 设置设备
            torch.cuda.set_device(rank)
            
        except Exception as e:
            logging.error(f"设置分布式环境失败: {str(e)}")
            raise
    
    def cleanup(self):
        """清理分布式环境"""
        dist.destroy_process_group()
    
    def train(self,
             model: torch.nn.Module,
             train_fn: Callable,
             user_id: int,
             training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分布式训练
        :param model: 模型实例
        :param train_fn: 训练函数
        :param user_id: 用户ID
        :param training_data: 训练数据
        :return: 训练结果
        """
        try:
            mp.spawn(
                self._train_worker,
                args=(model, train_fn, user_id, training_data),
                nprocs=self.world_size,
                join=True
            )
            
            # 收集并合并结果
            results = self._collect_results(user_id)
            
            return results
            
        except Exception as e:
            logging.error(f"分布式训练失败: {str(e)}")
            raise
    
    def _train_worker(self,
                     rank: int,
                     model: torch.nn.Module,
                     train_fn: Callable,
                     user_id: int,
                     training_data: Dict[str, Any]):
        """
        训练工作进程
        :param rank: 进程编号
        :param model: 模型实例
        :param train_fn: 训练函数
        :param user_id: 用户ID
        :param training_data: 训练数据
        """
        try:
            # 设置分布式环境
            self.setup(rank)
            
            # 准备模型
            model = model.to(rank)
            ddp_model = DDP(model, device_ids=[rank])
            
            # 准备数据
            train_sampler = self._prepare_distributed_data(training_data, rank)
            
            # 执行训练
            results = train_fn(
                ddp_model,
                training_data,
                train_sampler=train_sampler,
                device=rank
            )
            
            # 保存结果
            self._save_rank_results(results, rank, user_id)
            
            # 清理环境
            self.cleanup()
            
        except Exception as e:
            logging.error(f"训练工作进程失败: {str(e)}")
            raise
    
    def _prepare_distributed_data(self,
                                data: Dict[str, Any],
                                rank: int) -> torch.utils.data.distributed.DistributedSampler:
        """
        准备分布式数据
        :param data: 训练数据
        :param rank: 进程编号
        :return: 分布式采样器
        """
        try:
            # 创建数据集
            dataset = torch.utils.data.TensorDataset(
                *[torch.as_tensor(v) for v in data.values()]
            )
            
            # 创建分布式采样器
            sampler = torch.utils.data.distributed.DistributedSampler(
                dataset,
                num_replicas=self.world_size,
                rank=rank
            )
            
            return sampler
            
        except Exception as e:
            logging.error(f"准备分布式数据失败: {str(e)}")
            raise
    
    def _save_rank_results(self,
                          results: Dict[str, Any],
                          rank: int,
                          user_id: int):
        """
        保存进程结果
        :param results: 训练结果
        :param rank: 进程编号
        :param user_id: 用户ID
        """
        try:
            save_path = self.distributed_dir / f"rank_{rank}_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            with open(save_path / 'results.json', 'w') as f:
                json.dump({
                    **results,
                    'rank': rank,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存进程结果失败: {str(e)}")
            raise
    
    def _collect_results(self, user_id: int) -> Dict[str, Any]:
        """
        收集所有进程的结果
        :param user_id: 用户ID
        :return: 合并后的结果
        """
        try:
            all_results = []
            
            # 收集每个进程的结果
            for rank in range(self.world_size):
                result_path = self.distributed_dir / f"rank_{rank}_{user_id}" / 'results.json'
                with open(result_path, 'r') as f:
                    results = json.load(f)
                all_results.append(results)
            
            # 合并结果
            merged_results = self._merge_results(all_results)
            
            # 保存合并结果
            save_path = self.distributed_dir / f"merged_{user_id}"
            save_path.mkdir(parents=True, exist_ok=True)
            
            with open(save_path / 'merged_results.json', 'w') as f:
                json.dump(merged_results, f, indent=2)
            
            return merged_results
            
        except Exception as e:
            logging.error(f"收集结果失败: {str(e)}")
            raise
    
    def _merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个进程的结果
        :param results: 结果列表
        :return: 合并后的结果
        """
        try:
            merged = {}
            
            # 合并损失
            losses = [r.get('loss', 0) for r in results]
            merged['loss'] = sum(losses) / len(losses)
            
            # 合并指标
            metrics = {}
            for r in results:
                for k, v in r.get('metrics', {}).items():
                    if k not in metrics:
                        metrics[k] = []
                    metrics[k].append(v)
            
            merged['metrics'] = {
                k: sum(v) / len(v) for k, v in metrics.items()
            }
            
            # 添加训练信息
            merged['training_info'] = {
                'world_size': self.world_size,
                'backend': self.backend,
                'timestamp': datetime.now().isoformat()
            }
            
            return merged
            
        except Exception as e:
            logging.error(f"合并结果失败: {str(e)}")
            raise 