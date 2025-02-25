from typing import Dict, Any, Optional, Union, Callable
import logging
import json
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import hashlib
import pickle
from redis import Redis
from abc import ABC, abstractmethod

class CacheBackend(ABC):
    """缓存后端基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: bytes, expire: int = None):
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """删除缓存值"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

class RedisCache(CacheBackend):
    """Redis缓存后端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.client = Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0),
            password=config.get('redis_password'),
            decode_responses=False
        )
    
    def get(self, key: str) -> Optional[bytes]:
        try:
            return self.client.get(key)
        except Exception as e:
            logging.error(f"Redis获取缓存失败: {str(e)}")
            return None
    
    def set(self, key: str, value: bytes, expire: int = None):
        try:
            self.client.set(key, value, ex=expire)
        except Exception as e:
            logging.error(f"Redis设置缓存失败: {str(e)}")
    
    def delete(self, key: str):
        try:
            self.client.delete(key)
        except Exception as e:
            logging.error(f"Redis删除缓存失败: {str(e)}")
    
    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logging.error(f"Redis检查缓存失败: {str(e)}")
            return False

class MemoryCache(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self):
        self.cache: Dict[str, tuple] = {}  # (value, expire_time)
    
    def get(self, key: str) -> Optional[bytes]:
        try:
            if key in self.cache:
                value, expire_time = self.cache[key]
                if expire_time is None or datetime.now() < expire_time:
                    return value
                else:
                    del self.cache[key]
            return None
        except Exception as e:
            logging.error(f"内存获取缓存失败: {str(e)}")
            return None
    
    def set(self, key: str, value: bytes, expire: int = None):
        try:
            expire_time = None
            if expire is not None:
                expire_time = datetime.now() + timedelta(seconds=expire)
            self.cache[key] = (value, expire_time)
        except Exception as e:
            logging.error(f"内存设置缓存失败: {str(e)}")
    
    def delete(self, key: str):
        try:
            if key in self.cache:
                del self.cache[key]
        except Exception as e:
            logging.error(f"内存删除缓存失败: {str(e)}")
    
    def exists(self, key: str) -> bool:
        try:
            if key in self.cache:
                _, expire_time = self.cache[key]
                if expire_time is None or datetime.now() < expire_time:
                    return True
                else:
                    del self.cache[key]
            return False
        except Exception as e:
            logging.error(f"内存检查缓存失败: {str(e)}")
            return False

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_expire = config.get('cache_expire', 3600)  # 默认1小时
        
        # 初始化缓存后端
        backend_type = config.get('cache_backend', 'memory')
        if backend_type == 'redis':
            self.backend = RedisCache(config)
        else:
            self.backend = MemoryCache()
    
    def _generate_key(self, prefix: str, args: tuple, kwargs: Dict[str, Any]) -> str:
        """生成缓存键"""
        try:
            # 合并参数
            key_parts = [prefix]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            # 生成哈希
            key_str = "|".join(key_parts)
            return hashlib.md5(key_str.encode()).hexdigest()
            
        except Exception as e:
            logging.error(f"生成缓存键失败: {str(e)}")
            return prefix
    
    def cache(self,
             prefix: str,
             expire: Optional[int] = None,
             condition: Optional[Callable] = None):
        """
        缓存装饰器
        :param prefix: 键前缀
        :param expire: 过期时间(秒)
        :param condition: 缓存条件函数
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 检查缓存条件
                if condition and not condition(*args, **kwargs):
                    return await func(*args, **kwargs)
                
                # 生成缓存键
                cache_key = self._generate_key(prefix, args, kwargs)
                
                try:
                    # 尝试获取缓存
                    cached_value = self.backend.get(cache_key)
                    if cached_value is not None:
                        return pickle.loads(cached_value)
                    
                    # 执行函数
                    result = await func(*args, **kwargs)
                    
                    # 缓存结果
                    self.backend.set(
                        cache_key,
                        pickle.dumps(result),
                        expire or self.default_expire
                    )
                    
                    return result
                    
                except Exception as e:
                    logging.error(f"缓存操作失败: {str(e)}")
                    return await func(*args, **kwargs)
                
            return wrapper
        return decorator
    
    def invalidate(self, prefix: str, *args, **kwargs):
        """
        使缓存失效
        :param prefix: 键前缀
        :param args: 参数
        :param kwargs: 关键字参数
        """
        try:
            cache_key = self._generate_key(prefix, args, kwargs)
            self.backend.delete(cache_key)
        except Exception as e:
            logging.error(f"使缓存失效失败: {str(e)}")
    
    async def cleanup(self):
        """清理过期缓存"""
        try:
            if isinstance(self.backend, MemoryCache):
                current_time = datetime.now()
                expired_keys = [
                    key for key, (_, expire_time) in self.backend.cache.items()
                    if expire_time is not None and current_time >= expire_time
                ]
                for key in expired_keys:
                    self.backend.delete(key)
        except Exception as e:
            logging.error(f"清理缓存失败: {str(e)}")

# 缓存键前缀
CACHE_KEYS = {
    'prediction': 'pred',
    'training_status': 'train_status',
    'model_info': 'model_info',
    'visualization': 'viz'
} 