# coding:utf-8
"""
英雄评估器
基于多维度数据评估英雄强度
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

from .recommendation import Position, RecommendationReason


@dataclass
class EvaluationContext:
    """评估上下文"""
    champion_id: int
    position: Position
    ally_champions: List[int]          # 己方已选英雄
    enemy_champions: List[int]         # 敌方已选英雄
    enemy_bans: List[int]              # 敌方已禁英雄
    summoner_masteries: Dict[int, int] # 召唤师英雄熟练度 {champion_id: score}
    opgg_data: Optional[Dict] = None   # OP.GG 数据


class Evaluator(ABC):
    """评估器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """评估器名称"""
        pass

    @property
    def weight(self) -> float:
        """评估器权重，默认 1.0"""
        return 1.0

    @abstractmethod
    async def evaluate(self, context: EvaluationContext) -> float:
        """
        评估英雄，返回 0-100 的分数

        Args:
            context: 评估上下文

        Returns:
            评分 0-100
        """
        pass

    @abstractmethod
    def get_reasons(self, context: EvaluationContext, score: float) -> List[RecommendationReason]:
        """获取推荐理由"""
        pass


class TierEvaluator(Evaluator):
    """版本强度评估器"""

    @property
    def name(self) -> str:
        return "tier"

    @property
    def weight(self) -> float:
        return 1.5  # 版本强度权重较高

    def __init__(self):
        self.tier_data: Dict[int, Dict] = {}  # 缓存梯队数据

    async def evaluate(self, context: EvaluationContext) -> float:
        if not context.opgg_data:
            return 50.0  # 无数据时返回中值

        # 从 OP.GG 数据中获取梯队信息
        tier_list = context.opgg_data.get('tier_list', {})
        position_data = tier_list.get(context.position.value, [])

        for champion in position_data:
            if champion['championId'] == context.champion_id:
                tier = champion.get('tier', 4)
                rank = champion.get('rank', 999)
                win_rate = champion.get('winRate', 0.5)

                # 梯队转换为分数: T1=100, T2=80, T3=60, T4=40, T5=20
                tier_score = max(0, 120 - tier * 20)
                # 排名加成
                rank_bonus = max(0, (50 - rank) / 50 * 20)
                # 胜率调整
                win_adjust = (win_rate - 0.5) * 100

                return min(100, max(0, tier_score + rank_bonus + win_adjust))

        return 40.0  # 未在梯度榜中

    def get_reasons(self, context: EvaluationContext, score: float) -> List[RecommendationReason]:
        if score >= 80:
            return [RecommendationReason.TIER_STRONG]
        return []


class CounterEvaluator(Evaluator):
    """克制关系评估器"""

    @property
    def name(self) -> str:
        return "counter"

    @property
    def weight(self) -> float:
        return 1.2

    async def evaluate(self, context: EvaluationContext) -> float:
        if not context.opgg_data:
            return 50.0

        champion_data = context.opgg_data.get('champion_builds', {}).get(context.champion_id, {})
        counters = champion_data.get('counters', {})

        # 强势对抗的英雄列表
        strong_against = counters.get('strongAgainst', [])
        weak_against = counters.get('weakAgainst', [])

        score = 50.0

        # 检查是否克制敌方已选英雄
        for enemy_id in context.enemy_champions:
            for strong in strong_against:
                if strong['championId'] == enemy_id:
                    score += 15 * strong.get('winRate', 0.55)

        # 检查是否被敌方克制
        for enemy_id in context.enemy_champions:
            for weak in weak_against:
                if weak['championId'] == enemy_id:
                    score -= 15 * (1 - weak.get('winRate', 0.45))

        return min(100, max(0, score))

    def get_reasons(self, context: EvaluationContext, score: float) -> List[RecommendationReason]:
        if score >= 70:
            return [RecommendationReason.COUNTER_ENEMY]
        return []


class SynergyEvaluator(Evaluator):
    """阵容配合评估器"""

    @property
    def name(self) -> str:
        return "synergy"

    @property
    def weight(self) -> float:
        return 0.8

    async def evaluate(self, context: EvaluationContext) -> float:
        # TODO: 实现阵容配合评估
        # 1. 检查与队友的控制链配合
        # 2. 检查伤害类型平衡（AP/AD）
        # 3. 检查前后排保护关系

        score = 50.0

        # 简化实现：检查是否有配合数据
        if context.opgg_data:
            champion_data = context.opgg_data.get('champion_builds', {}).get(context.champion_id, {})
            # 如果有 synergies 数据，使用它
            synergies = champion_data.get('synergies', [])
            for syn in synergies:
                if syn['championId'] in context.ally_champions:
                    score += 10 * syn.get('winRate', 0.5)

        return min(100, max(0, score))

    def get_reasons(self, context: EvaluationContext, score: float) -> List[RecommendationReason]:
        if score >= 65:
            return [RecommendationReason.SYNERGY_ALLY]
        return []


class MasteryEvaluator(Evaluator):
    """个人熟练度评估器"""

    @property
    def name(self) -> str:
        return "mastery"

    @property
    def weight(self) -> float:
        return 1.0  # 可通过配置调整

    async def evaluate(self, context: EvaluationContext) -> float:
        mastery = context.summoner_masteries.get(context.champion_id, 0)

        if mastery == 0:
            return 20.0  # 无熟练度

        # 熟练度转换为分数
        # 0-10000: 20-40
        # 10000-50000: 40-60
        # 50000-100000: 60-80
        # 100000+: 80-100

        if mastery < 10000:
            return 20 + (mastery / 10000) * 20
        elif mastery < 50000:
            return 40 + ((mastery - 10000) / 40000) * 20
        elif mastery < 100000:
            return 60 + ((mastery - 50000) / 50000) * 20
        else:
            return min(100, 80 + ((mastery - 100000) / 100000) * 10)

    def get_reasons(self, context: EvaluationContext, score: float) -> List[RecommendationReason]:
        if score >= 70:
            return [RecommendationReason.HIGH_MASTERY]
        return []


class ChampionEvaluator:
    """
    英雄综合评估器
    整合多个评估器的结果
    """

    def __init__(self):
        self.evaluators: List[Evaluator] = [
            TierEvaluator(),
            CounterEvaluator(),
            SynergyEvaluator(),
            MasteryEvaluator()
        ]
        self.weights: Dict[str, float] = {}

        # 计算权重总和
        self._update_weights()

    def _update_weights(self):
        """更新权重"""
        total = sum(e.weight for e in self.evaluators)
        for e in self.evaluators:
            self.weights[e.name] = e.weight / total

    def add_evaluator(self, evaluator: Evaluator):
        """添加评估器"""
        self.evaluators.append(evaluator)
        self._update_weights()

    async def evaluate(self, context: EvaluationContext) -> Dict[str, float]:
        """
        执行综合评估

        Returns:
            {
                'total': 总分,
                'tier': 版本分,
                'counter': 克制分,
                'synergy': 配合分,
                'mastery': 熟练度分,
                'reasons': 推荐理由
            }
        """
        results = {}
        total = 0.0

        for evaluator in self.evaluators:
            score = await evaluator.evaluate(context)
            weighted_score = score * self.weights[evaluator.name]
            results[evaluator.name] = score
            total += weighted_score

        # 收集推荐理由
        reasons = []
        for evaluator in self.evaluators:
            score = results[evaluator.name]
            reasons.extend(evaluator.get_reasons(context, score))

        results['total'] = total
        results['reasons'] = reasons

        return results
