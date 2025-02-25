import torch
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import shutil
import os

class ModelManager:
    """模型管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_dir = Path(config['model_dir'])
        self.max_versions = config.get('max_versions', 3)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 创建模型目录
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def save_model(self,
                  model: torch.nn.Module,
                  model_info: Dict[str, Any],
                  user_id: int,
                  model_type: str) -> str:
        """
        保存模型
        :param model: 模型实例
        :param model_info: 模型信息
        :param user_id: 用户ID
        :param model_type: 模型类型 ('student' 或 'teacher')
        :return: 模型版本ID
        """
        try:
            # 生成版本ID
            version_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 创建保存目录
            save_dir = self.model_dir / f"{model_type}_{user_id}" / version_id
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存模型状态
            model_path = save_dir / 'model.pth'
            torch.save({
                'state_dict': model.state_dict(),
                'config': model.config if hasattr(model, 'config') else {},
                'version': version_id,
                'timestamp': datetime.now().isoformat()
            }, model_path)
            
            # 保存模型信息
            info_path = save_dir / 'info.json'
            with open(info_path, 'w') as f:
                json.dump({
                    **model_info,
                    'version': version_id,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # 清理旧版本
            self._cleanup_old_versions(model_type, user_id)
            
            return version_id
            
        except Exception as e:
            logging.error(f"保存模型失败: {str(e)}")
            raise
    
    def load_model(self,
                  model_class: type,
                  user_id: int,
                  model_type: str,
                  version_id: Optional[str] = None) -> Tuple[torch.nn.Module, Dict[str, Any]]:
        """
        加载模型
        :param model_class: 模型类
        :param user_id: 用户ID
        :param model_type: 模型类型
        :param version_id: 版本ID (None表示最新版本)
        :return: (模型实例, 模型信息)
        """
        try:
            # 获取模型版本路径
            version_path = self._get_version_path(model_type, user_id, version_id)
            if not version_path:
                raise FileNotFoundError(f"未找到模型: {model_type}_{user_id}")
            
            # 加载模型状态
            model_path = version_path / 'model.pth'
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # 创建模型实例
            model = model_class(checkpoint['config'])
            model.load_state_dict(checkpoint['state_dict'])
            model.to(self.device)
            
            # 加载模型信息
            info_path = version_path / 'info.json'
            with open(info_path, 'r') as f:
                model_info = json.load(f)
            
            return model, model_info
            
        except Exception as e:
            logging.error(f"加载模型失败: {str(e)}")
            raise
    
    def get_model_info(self,
                      user_id: int,
                      model_type: str,
                      version_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取模型信息
        :param user_id: 用户ID
        :param model_type: 模型类型
        :param version_id: 版本ID
        :return: 模型信息
        """
        try:
            version_path = self._get_version_path(model_type, user_id, version_id)
            if not version_path:
                return None
            
            info_path = version_path / 'info.json'
            with open(info_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logging.error(f"获取模型信息失败: {str(e)}")
            return None
    
    def list_versions(self,
                     user_id: int,
                     model_type: str) -> List[Dict[str, Any]]:
        """
        列出模型版本
        :param user_id: 用户ID
        :param model_type: 模型类型
        :return: 版本信息列表
        """
        try:
            model_path = self.model_dir / f"{model_type}_{user_id}"
            if not model_path.exists():
                return []
            
            versions = []
            for version_dir in sorted(model_path.iterdir(), reverse=True):
                if version_dir.is_dir():
                    info_path = version_dir / 'info.json'
                    if info_path.exists():
                        with open(info_path, 'r') as f:
                            versions.append(json.load(f))
            
            return versions
            
        except Exception as e:
            logging.error(f"列出模型版本失败: {str(e)}")
            return []
    
    def delete_version(self,
                      user_id: int,
                      model_type: str,
                      version_id: str) -> bool:
        """
        删除模型版本
        :param user_id: 用户ID
        :param model_type: 模型类型
        :param version_id: 版本ID
        :return: 是否删除成功
        """
        try:
            version_path = self.model_dir / f"{model_type}_{user_id}" / version_id
            if version_path.exists():
                shutil.rmtree(version_path)
                return True
            return False
            
        except Exception as e:
            logging.error(f"删除模型版本失败: {str(e)}")
            return False
    
    def _get_version_path(self,
                         model_type: str,
                         user_id: int,
                         version_id: Optional[str] = None) -> Optional[Path]:
        """获取版本路径"""
        try:
            model_path = self.model_dir / f"{model_type}_{user_id}"
            if not model_path.exists():
                return None
            
            if version_id:
                version_path = model_path / version_id
                return version_path if version_path.exists() else None
            
            # 获取最新版本
            versions = sorted(
                [d for d in model_path.iterdir() if d.is_dir()],
                key=lambda x: x.name,
                reverse=True
            )
            return versions[0] if versions else None
            
        except Exception as e:
            logging.error(f"获取版本路径失败: {str(e)}")
            return None
    
    def _cleanup_old_versions(self, model_type: str, user_id: int):
        """清理旧版本"""
        try:
            model_path = self.model_dir / f"{model_type}_{user_id}"
            if not model_path.exists():
                return
            
            # 获取所有版本
            versions = sorted(
                [d for d in model_path.iterdir() if d.is_dir()],
                key=lambda x: x.name,
                reverse=True
            )
            
            # 删除超出限制的旧版本
            if len(versions) > self.max_versions:
                for version_dir in versions[self.max_versions:]:
                    shutil.rmtree(version_dir)
                    
        except Exception as e:
            logging.error(f"清理旧版本失败: {str(e)}") 