import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
from datetime import datetime, timedelta

class ResourceMatcher:
    """资源推荐匹配器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vectorizer = TfidfVectorizer(
            max_features=config.get('max_features', 1000),
            stop_words='english'
        )
        self.cache = {}  # 简单的内存缓存
        self.cache_ttl = config.get('cache_ttl', 3600)  # 缓存过期时间(秒)
    
    def recommend_resources(self, 
                          user_profile: Dict[str, Any],
                          available_resources: List[Dict[str, Any]],
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        推荐资源
        :param user_profile: 用户画像(包含薄弱点、兴趣点等)
        :param available_resources: 可用资源列表
        :param top_k: 返回推荐数量
        :return: 推荐资源列表
        """
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(user_profile, top_k)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # 计算内容相似度分数
            content_scores = self._calculate_content_similarity(
                user_profile,
                available_resources
            )
            
            # 计算协同过滤分数
            cf_scores = self._calculate_collaborative_filtering(
                user_profile,
                available_resources
            )
            
            # 合并分数
            final_scores = self._combine_scores(content_scores, cf_scores)
            
            # 选择top-k资源
            recommended_indices = np.argsort(final_scores)[-top_k:][::-1]
            recommendations = [
                self._enrich_resource(available_resources[i], final_scores[i])
                for i in recommended_indices
            ]
            
            # 更新缓存
            self._add_to_cache(cache_key, recommendations)
            
            return recommendations
            
        except Exception as e:
            logging.error(f"资源推荐失败: {str(e)}")
            return []
    
    def _calculate_content_similarity(self,
                                   user_profile: Dict[str, Any],
                                   resources: List[Dict[str, Any]]) -> np.ndarray:
        """计算内容相似度"""
        try:
            # 提取用户特征
            user_features = self._extract_user_features(user_profile)
            
            # 提取资源特征
            resource_features = [
                self._extract_resource_features(resource)
                for resource in resources
            ]
            
            # 转换为TF-IDF向量
            all_features = [user_features] + resource_features
            feature_matrix = self.vectorizer.fit_transform(all_features)
            
            # 计算余弦相似度
            similarities = cosine_similarity(
                feature_matrix[0:1],
                feature_matrix[1:]
            )[0]
            
            return similarities
            
        except Exception as e:
            logging.error(f"计算内容相似度失败: {str(e)}")
            return np.zeros(len(resources))
    
    def _calculate_collaborative_filtering(self,
                                        user_profile: Dict[str, Any],
                                        resources: List[Dict[str, Any]]) -> np.ndarray:
        """计算协同过滤分数"""
        try:
            # 获取用户历史交互
            user_history = user_profile.get('resource_history', [])
            if not user_history:
                return np.zeros(len(resources))
            
            # 计算资源相似度矩阵
            resource_features = [
                self._extract_resource_features(resource)
                for resource in resources
            ]
            feature_matrix = self.vectorizer.fit_transform(resource_features)
            resource_similarities = cosine_similarity(feature_matrix)
            
            # 基于历史交互计算分数
            scores = np.zeros(len(resources))
            for hist_resource in user_history:
                if hist_resource['feedback'] > 0:  # 只考虑正面反馈
                    for i, resource in enumerate(resources):
                        sim_score = self._calculate_resource_similarity(
                            hist_resource,
                            resource
                        )
                        scores[i] += sim_score * hist_resource['feedback']
            
            return scores / (len(user_history) + 1e-10)  # 避免除零
            
        except Exception as e:
            logging.error(f"计算协同过滤分数失败: {str(e)}")
            return np.zeros(len(resources))
    
    def _combine_scores(self,
                       content_scores: np.ndarray,
                       cf_scores: np.ndarray) -> np.ndarray:
        """合并不同来源的分数"""
        # 根据配置的权重合并
        content_weight = self.config.get('content_weight', 0.7)
        cf_weight = self.config.get('cf_weight', 0.3)
        
        # 归一化
        content_scores = self._normalize_scores(content_scores)
        cf_scores = self._normalize_scores(cf_scores)
        
        return content_weight * content_scores + cf_weight * cf_scores
    
    def _extract_user_features(self, user_profile: Dict[str, Any]) -> str:
        """提取用户特征文本"""
        features = []
        
        # 添加薄弱点
        if 'weaknesses' in user_profile:
            features.extend(user_profile['weaknesses'])
            
        # 添加兴趣点
        if 'interests' in user_profile:
            features.extend(user_profile['interests'])
            
        # 添加学习目标
        if 'learning_goals' in user_profile:
            features.extend(user_profile['learning_goals'])
            
        return ' '.join(features)
    
    def _extract_resource_features(self, resource: Dict[str, Any]) -> str:
        """提取资源特征文本"""
        features = []
        
        # 添加标题
        if 'title' in resource:
            features.append(resource['title'])
            
        # 添加描述
        if 'description' in resource:
            features.append(resource['description'])
            
        # 添加标签
        if 'tags' in resource:
            features.extend(resource['tags'])
            
        return ' '.join(features)
    
    def _calculate_resource_similarity(self,
                                    resource1: Dict[str, Any],
                                    resource2: Dict[str, Any]) -> float:
        """计算两个资源之间的相似度"""
        try:
            # 提取特征
            features1 = self._extract_resource_features(resource1)
            features2 = self._extract_resource_features(resource2)
            
            # 转换为TF-IDF向量
            vectors = self.vectorizer.fit_transform([features1, features2])
            
            # 计算余弦相似度
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logging.error(f"计算资源相似度失败: {str(e)}")
            return 0.0
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """归一化分数"""
        if len(scores) == 0:
            return scores
        score_min = scores.min()
        score_max = scores.max()
        if score_max - score_min > 1e-10:
            return (scores - score_min) / (score_max - score_min)
        return scores
    
    def _enrich_resource(self,
                        resource: Dict[str, Any],
                        score: float) -> Dict[str, Any]:
        """丰富资源信息"""
        enriched = resource.copy()
        enriched['recommendation_score'] = float(score)
        enriched['recommendation_reason'] = self._generate_recommendation_reason(
            resource,
            score
        )
        return enriched
    
    def _generate_recommendation_reason(self,
                                     resource: Dict[str, Any],
                                     score: float) -> str:
        """生成推荐原因"""
        reasons = []
        
        if score > 0.8:
            reasons.append("非常匹配您的学习需求")
        elif score > 0.6:
            reasons.append("比较适合您当前的学习阶段")
            
        if resource.get('rating', 0) > 4.5:
            reasons.append("深受其他学习者好评")
            
        if resource.get('difficulty') == 'adaptive':
            reasons.append("难度会自动适应您的水平")
            
        return '，'.join(reasons) if reasons else "根据您的学习特点推荐"
    
    def _generate_cache_key(self,
                          user_profile: Dict[str, Any],
                          top_k: int) -> str:
        """生成缓存键"""
        profile_str = f"{user_profile.get('id')}_{top_k}"
        return f"resource_recommendations_{profile_str}"
    
    def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """从缓存获取结果"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return data
            else:
                del self.cache[key]
        return None
    
    def _add_to_cache(self, key: str, data: List[Dict[str, Any]]):
        """添加结果到缓存"""
        self.cache[key] = (data, datetime.now()) 