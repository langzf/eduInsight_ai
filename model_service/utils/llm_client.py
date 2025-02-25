import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from functools import lru_cache
import os
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.cache_ttl = config.get('cache_ttl', 3600)
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        pass
    
    @abstractmethod
    async def analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """分析文本"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """生成文本嵌入"""
        pass

class xAIClient(BaseLLMClient):
    """xAI API客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = None
        self._cache = {}
    
    async def _ensure_session(self):
        """确保aiohttp会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成文本
        :param prompt: 提示文本
        :param kwargs: 其他参数
        :return: 生成结果
        """
        try:
            # 检查缓存
            cache_key = f"generate_{prompt}_{json.dumps(kwargs)}"
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            await self._ensure_session()
            
            # 准备请求数据
            data = {
                'prompt': prompt,
                'max_tokens': kwargs.get('max_tokens', 100),
                'temperature': kwargs.get('temperature', 0.7),
                'model': kwargs.get('model', 'grok-3')
            }
            
            # 发送请求
            for attempt in range(self.max_retries):
                try:
                    async with self.session.post(
                        f"{self.base_url}/generate",
                        json=data,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            # 缓存结果
                            self._add_to_cache(cache_key, result)
                            return result
                        else:
                            error_msg = await response.text()
                            logging.error(f"xAI API错误: {error_msg}")
                            
                except asyncio.TimeoutError:
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1)
                    
            raise Exception("所有重试都失败了")
            
        except Exception as e:
            logging.error(f"生成文本失败: {str(e)}")
            raise
    
    async def analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        分析文本
        :param text: 待分析文本
        :param kwargs: 其他参数
        :return: 分析结果
        """
        try:
            # 检查缓存
            cache_key = f"analyze_{text}_{json.dumps(kwargs)}"
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            await self._ensure_session()
            
            # 准备请求数据
            data = {
                'text': text,
                'analysis_type': kwargs.get('analysis_type', 'general'),
                'model': kwargs.get('model', 'grok-3')
            }
            
            # 发送请求
            async with self.session.post(
                f"{self.base_url}/analyze",
                json=data,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # 缓存结果
                    self._add_to_cache(cache_key, result)
                    return result
                else:
                    error_msg = await response.text()
                    raise Exception(f"xAI API错误: {error_msg}")
                    
        except Exception as e:
            logging.error(f"分析文本失败: {str(e)}")
            raise
    
    @lru_cache(maxsize=1000)
    async def embed(self, text: str) -> List[float]:
        """
        生成文本嵌入
        :param text: 输入文本
        :return: 嵌入向量
        """
        try:
            await self._ensure_session()
            
            # 准备请求数据
            data = {
                'text': text,
                'model': 'grok-3-embedding'
            }
            
            # 发送请求
            async with self.session.post(
                f"{self.base_url}/embeddings",
                json=data,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['embedding']
                else:
                    error_msg = await response.text()
                    raise Exception(f"xAI API错误: {error_msg}")
                    
        except Exception as e:
            logging.error(f"生成嵌入失败: {str(e)}")
            raise
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取结果"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _add_to_cache(self, key: str, data: Dict[str, Any]):
        """添加结果到缓存"""
        self._cache[key] = (data, datetime.now())
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()

class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create_client(provider: str, config: Dict[str, Any]) -> BaseLLMClient:
        """
        创建LLM客户端
        :param provider: 提供商名称
        :param config: 配置信息
        :return: LLM客户端实例
        """
        if provider == 'xai':
            return xAIClient(config)
        # TODO: 添加其他LLM提供商的支持
        raise ValueError(f"不支持的LLM提供商: {provider}")

# 使用示例
async def analyze_homework(homework_text: str) -> Dict[str, Any]:
    """分析作业内容"""
    try:
        # 创建LLM客户端
        config = {
            'api_key': os.getenv('XAI_API_KEY'),
            'base_url': 'https://api.xai.com/v1',
            'timeout': 30,
            'max_retries': 3
        }
        client = LLMClientFactory.create_client('xai', config)
        
        # 分析作业
        result = await client.analyze(
            homework_text,
            analysis_type='homework',
            model='grok-3'
        )
        
        # 关闭客户端
        await client.close()
        
        return result
        
    except Exception as e:
        logging.error(f"分析作业失败: {str(e)}")
        raise

async def generate_feedback(analysis_result: Dict[str, Any]) -> str:
    """生成反馈建议"""
    try:
        # 创建LLM客户端
        config = {
            'api_key': os.getenv('XAI_API_KEY'),
            'base_url': 'https://api.xai.com/v1',
            'timeout': 30,
            'max_retries': 3
        }
        client = LLMClientFactory.create_client('xai', config)
        
        # 构建提示
        prompt = f"""
        基于以下分析结果生成教学建议:
        薄弱点: {analysis_result.get('weaknesses', [])}
        错误类型: {analysis_result.get('error_types', [])}
        请提供具体的改进建议。
        """
        
        # 生成建议
        result = await client.generate(
            prompt,
            max_tokens=200,
            temperature=0.7
        )
        
        # 关闭客户端
        await client.close()
        
        return result['text']
        
    except Exception as e:
        logging.error(f"生成反馈建议失败: {str(e)}")
        raise 