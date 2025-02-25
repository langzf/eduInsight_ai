from typing import List, Optional
import aiohttp
from app.core.config import settings

class ContentCheckResult:
    def __init__(
        self,
        safe: bool,
        sensitive_words: List[str],
        similarity: float,
        quality: float,
        recommendation: str
    ):
        self.safe = safe
        self.sensitive_words = sensitive_words
        self.similarity = similarity
        self.quality = quality
        self.recommendation = recommendation

class ContentChecker:
    def __init__(self):
        self.sensitive_api = settings.SENSITIVE_CHECK_API
        self.similarity_api = settings.SIMILARITY_CHECK_API
        self.quality_api = settings.QUALITY_CHECK_API
    
    async def check(self, url: str) -> ContentCheckResult:
        """检查内容"""
        async with aiohttp.ClientSession() as session:
            # 1. 敏感词检查
            sensitive_words = await self._check_sensitive(session, url)
            
            # 2. 相似度检查
            similarity = await self._check_similarity(session, url)
            
            # 3. 质量评估
            quality = await self._check_quality(session, url)
            
            # 4. 生成建议
            safe = len(sensitive_words) == 0
            recommendation = self._get_recommendation(
                safe,
                similarity,
                quality
            )
            
            return ContentCheckResult(
                safe=safe,
                sensitive_words=sensitive_words,
                similarity=similarity,
                quality=quality,
                recommendation=recommendation
            )
    
    async def _check_sensitive(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> List[str]:
        """敏感词检查"""
        async with session.post(self.sensitive_api, json={"url": url}) as resp:
            result = await resp.json()
            return result.get("sensitive_words", [])
    
    async def _check_similarity(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> float:
        """相似度检查"""
        async with session.post(self.similarity_api, json={"url": url}) as resp:
            result = await resp.json()
            return result.get("similarity", 0.0)
    
    async def _check_quality(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> float:
        """质量评估"""
        async with session.post(self.quality_api, json={"url": url}) as resp:
            result = await resp.json()
            return result.get("quality", 0.0)
    
    def _get_recommendation(
        self,
        safe: bool,
        similarity: float,
        quality: float
    ) -> str:
        """生成审核建议"""
        if not safe:
            return "reject"
        if similarity > 0.8:
            return "reject"
        if quality < 0.3:
            return "reject"
        if quality > 0.7:
            return "approve"
        return "manual" 