# coding:utf-8
"""
推荐结果数据结构定义
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Position(Enum):
    """位置枚举"""
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MID = "MID"
    ADC = "ADC"
    SUPPORT = "SUPPORT"
    FILL = "FILL"


class RecommendationReason(Enum):
    """推荐理由枚举"""
    TIER_STRONG = "版本强势"
    COUNTER_ENEMY = "克制敌方"
    SYNERGY_ALLY = "配合队友"
    HIGH_MASTERY = "熟练度高"
    ENEMY_WEAK = "敌方弱势"
    POSITION_NEED = "位置需求"
    BAN_THREAT = "威胁己方"
    ENEMY_MASTERY = "敌方擅长"


@dataclass
class BanRecommendation:
    """Ban 推荐结果"""
    champion_id: int
    champion_name: str
    priority: float                    # 0-100 推荐优先级
    reasons: List[RecommendationReason]
    threat_score: float = 0.0          # 威胁程度
    enemy_mastery: Optional[int] = None  # 敌方熟练度（如果检测到）

    def to_dict(self) -> dict:
        return {
            'champion_id': self.champion_id,
            'champion_name': self.champion_name,
            'priority': self.priority,
            'reasons': [r.value for r in self.reasons],
            'threat_score': self.threat_score,
            'enemy_mastery': self.enemy_mastery
        }


@dataclass
class PickRecommendation:
    """Pick 推荐结果"""
    champion_id: int
    champion_name: str
    position: Position
    priority: float                    # 0-100 推荐优先级
    reasons: List[RecommendationReason]

    # 各维度评分
    tier_score: float = 0.0            # 版本强度分
    counter_score: float = 0.0         # 克制关系分
    synergy_score: float = 0.0         # 阵容配合分
    mastery_score: float = 0.0         # 个人熟练度分

    # 详细信息
    win_rate: Optional[float] = None   # OP.GG 胜率
    pick_rate: Optional[float] = None  # OP.GG 选取率

    def to_dict(self) -> dict:
        return {
            'champion_id': self.champion_id,
            'champion_name': self.champion_name,
            'position': self.position.value,
            'priority': self.priority,
            'reasons': [r.value for r in self.reasons],
            'scores': {
                'tier': self.tier_score,
                'counter': self.counter_score,
                'synergy': self.synergy_score,
                'mastery': self.mastery_score
            },
            'win_rate': self.win_rate,
            'pick_rate': self.pick_rate
        }


@dataclass
class TeamComposition:
    """阵容分析"""
    engage_score: float = 0.0          # 开团能力
    poke_score: float = 0.0            # Poke能力
    peel_score: float = 0.0            # 保护能力
    split_push_score: float = 0.0      # 分推能力
    team_fight_score: float = 0.0      # 团战能力
    early_game_score: float = 0.0      # 前期能力
    late_game_score: float = 0.0       # 后期能力

    def to_dict(self) -> dict:
        return {
            'engage': self.engage_score,
            'poke': self.poke_score,
            'peel': self.peel_score,
            'split_push': self.split_push_score,
            'team_fight': self.team_fight_score,
            'early_game': self.early_game_score,
            'late_game': self.late_game_score
        }


@dataclass
class CompositionAnalysis:
    """阵容对比分析"""
    ally_composition: TeamComposition
    enemy_composition: TeamComposition
    advantages: List[str]              # 己方优势
    disadvantages: List[str]           # 己方劣势
    suggestions: List[str]             # 战术建议

    def to_dict(self) -> dict:
        return {
            'ally': self.ally_composition.to_dict(),
            'enemy': self.enemy_composition.to_dict(),
            'advantages': self.advantages,
            'disadvantages': self.disadvantages,
            'suggestions': self.suggestions
        }


@dataclass
class Recommendation:
    """完整推荐结果"""
    ban_recommendations: List[BanRecommendation]
    pick_recommendations: List[PickRecommendation]
    composition_analysis: Optional[CompositionAnalysis] = None
    current_phase: str = ""            # 当前 BP 阶段
    current_position: str = ""         # 当前需要填充的位置

    def to_dict(self) -> dict:
        return {
            'bans': [b.to_dict() for b in self.ban_recommendations],
            'picks': [p.to_dict() for p in self.pick_recommendations],
            'composition': self.composition_analysis.to_dict() if self.composition_analysis else None,
            'phase': self.current_phase,
            'position': self.current_position
        }
