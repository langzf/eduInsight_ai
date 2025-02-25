import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from functools import lru_cache

class DataFetcher:
    """数据获取器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['service_url']
        self.api_key = config['api_key']
        self.timeout = config.get('timeout', 30)
        self.session = None
        self._cache = {}
        self.cache_ttl = config.get('cache_ttl', 300)  # 5分钟缓存
    
    async def _ensure_session(self):
        """确保aiohttp会话存在"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
    
    async def get_student_data(self, 
                             student_id: int,
                             homework_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取学生数据
        :param student_id: 学生ID
        :param homework_id: 作业ID（可选）
        :return: 学生数据
        """
        try:
            await self._ensure_session()
            
            # 构建请求URL
            url = f"{self.base_url}/api/v1/students/{student_id}/data"
            if homework_id:
                url += f"?homework_id={homework_id}"
            
            # 发送请求
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 处理数据
                    processed_data = {
                        'text': self._process_text_data(data),
                        'sequence': self._process_sequence_data(data),
                        'metadata': {
                            'student_id': student_id,
                            'homework_id': homework_id,
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    return processed_data
                else:
                    error_msg = await response.text()
                    raise Exception(f"获取学生数据失败: {error_msg}")
                    
        except Exception as e:
            logging.error(f"获取学生数据失败: {str(e)}")
            raise
    
    async def get_teacher_data(self, teacher_id: int) -> Dict[str, Any]:
        """
        获取教师数据
        :param teacher_id: 教师ID
        :return: 教师数据
        """
        try:
            await self._ensure_session()
            
            # 获取基本信息
            url = f"{self.base_url}/api/v1/teachers/{teacher_id}/data"
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    basic_data = await response.json()
                else:
                    error_msg = await response.text()
                    raise Exception(f"获取教师数据失败: {error_msg}")
            
            # 获取教学记录
            url = f"{self.base_url}/api/v1/teachers/{teacher_id}/teaching_records"
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    teaching_records = await response.json()
                else:
                    teaching_records = []
            
            # 处理数据
            processed_data = {
                'content': self._process_teaching_content(basic_data, teaching_records),
                'student_data': await self._get_class_students_data(basic_data['class_ids']),
                'metadata': {
                    'teacher_id': teacher_id,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            return processed_data
            
        except Exception as e:
            logging.error(f"获取教师数据失败: {str(e)}")
            raise
    
    async def get_user_profile(self, user_id: int, user_type: str) -> Dict[str, Any]:
        """
        获取用户画像
        :param user_id: 用户ID
        :param user_type: 用户类型
        :return: 用户画像
        """
        try:
            # 检查缓存
            cache_key = f"profile_{user_type}_{user_id}"
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            await self._ensure_session()
            
            url = f"{self.base_url}/api/v1/users/{user_id}/profile"
            params = {'user_type': user_type}
            
            async with self.session.get(url, params=params, timeout=self.timeout) as response:
                if response.status == 200:
                    profile = await response.json()
                    
                    # 添加到缓存
                    self._add_to_cache(cache_key, profile)
                    
                    return profile
                else:
                    error_msg = await response.text()
                    raise Exception(f"获取用户画像失败: {error_msg}")
                    
        except Exception as e:
            logging.error(f"获取用户画像失败: {str(e)}")
            raise
    
    async def get_available_resources(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取可用资源
        :param filters: 过滤条件
        :return: 资源列表
        """
        try:
            await self._ensure_session()
            
            url = f"{self.base_url}/api/v1/resources"
            async with self.session.get(url, params=filters, timeout=self.timeout) as response:
                if response.status == 200:
                    resources = await response.json()
                    return resources
                else:
                    error_msg = await response.text()
                    raise Exception(f"获取资源失败: {error_msg}")
                    
        except Exception as e:
            logging.error(f"获取资源失败: {str(e)}")
            raise
    
    def _process_text_data(self, data: Dict[str, Any]) -> str:
        """处理文本数据"""
        text_parts = []
        
        # 添加作业内容
        if 'homework' in data:
            text_parts.append(data['homework'].get('content', ''))
        
        # 添加问答记录
        if 'qa_records' in data:
            for qa in data['qa_records']:
                text_parts.append(f"Q: {qa['question']}")
                text_parts.append(f"A: {qa['answer']}")
        
        return '\n'.join(text_parts)
    
    def _process_sequence_data(self, data: Dict[str, Any]) -> List[float]:
        """处理序列数据"""
        sequence = []
        
        # 添加成绩数据
        if 'scores' in data:
            sequence.extend([score['value'] for score in data['scores']])
        
        # 添加参与度数据
        if 'participation' in data:
            sequence.extend([p['value'] for p in data['participation']])
        
        return sequence
    
    def _process_teaching_content(self,
                                basic_data: Dict[str, Any],
                                teaching_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理教学内容"""
        content = {
            'plans': basic_data.get('teaching_plans', []),
            'recordings': [],
            'feedback': []
        }
        
        # 处理教学记录
        for record in teaching_records:
            if record.get('type') == 'recording':
                content['recordings'].append(record['content'])
            elif record.get('type') == 'feedback':
                content['feedback'].append(record['content'])
        
        return content
    
    async def _get_class_students_data(self, class_ids: List[int]) -> List[Dict[str, Any]]:
        """获取班级学生数据"""
        students_data = []
        
        for class_id in class_ids:
            url = f"{self.base_url}/api/v1/classes/{class_id}/students"
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    class_students = await response.json()
                    students_data.extend(class_students)
        
        return students_data
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _add_to_cache(self, key: str, data: Dict[str, Any]):
        """添加数据到缓存"""
        self._cache[key] = (data, datetime.now())
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close() 