# coding:utf-8
"""
阵容分析器
分析双方阵容的优劣势
"""
from typing import List, Dict, Optional
from dataclasses import dataclass

from .recommendation import TeamComposition, CompositionAnalysis


@dataclass
class ChampionRole:
    """英雄角色定位"""
    champion_id: int
    primary_role: str       # 主定位: tank, fighter, assassin, mage, marksman, support
    secondary_role: str     # 副定位
    damage_type: str        # 伤害类型: ad, ap, true, mixed


class TeamAnalyzer:
    """
    阵容分析器
    分析阵容特点和优劣势
    """

    # 英雄角色数据（简化版，实际应从数据文件加载）
    CHAMPION_ROLES: Dict[int, ChampionRole] = {}

    def __init__(self, connector):
        self.connector = connector
        self._load_champion_roles()

    def _load_champion_roles(self):
        """加载英雄角色数据"""
        # TODO: 从本地数据文件或 API 加载完整的英雄定位数据
        pass

    async def analyze(self, ally_champions: List[int],
                      enemy_champions: List[int]) -> CompositionAnalysis:
        """
        分析双方阵容

        Args:
            ally_champions: 己方英雄 ID 列表
            enemy_champions: 敌方英雄 ID 列表

        Returns:
            阵容分析结果
        """
        ally_comp = await self._analyze_composition(ally_champions)
        enemy_comp = await self._analyze_composition(enemy_champions)

        advantages = self._find_advantages(ally_comp, enemy_comp)
        disadvantages = self._find_disadvantages(ally_comp, enemy_comp)
        suggestions = self._generate_suggestions(ally_comp, enemy_comp)

        return CompositionAnalysis(
            ally_composition=ally_comp,
            enemy_composition=enemy_comp,
            advantages=advantages,
            disadvantages=disadvantages,
            suggestions=suggestions
        )

    async def _analyze_composition(self, champions: List[int]) -> TeamComposition:
        """分析单个阵容"""
        if not champions:
            return TeamComposition()

        # 统计各维度能力
        engage = 0.0
        poke = 0.0
        peel = 0.0
        split_push = 0.0
        team_fight = 0.0
        early_game = 0.0
        late_game = 0.0

        for champion_id in champions:
            role = self.CHAMPION_ROLES.get(champion_id)
            if not role:
                continue

            # 根据角色类型累加能力值
            if role.primary_role == 'tank':
                engage += 15
                peel += 20
                team_fight += 10
            elif role.primary_role == 'fighter':
                engage += 10
                split_push += 15
                team_fight += 10
            elif role.primary_role == 'assassin':
                engage += 5
                split_push += 10
                early_game += 15
            elif role.primary_role == 'mage':
                poke += 15
                team_fight += 20
                late_game += 10
            elif role.primary_role == 'marksman':
                team_fight += 15
                late_game += 20
                split_push += 10
            elif role.primary_role == 'support':
                engage += 10
                peel += 25
                team_fight += 10

        # 归一化到 0-100
        count = len(champions)
        return TeamComposition(
            engage_score=min(100, engage / count * 10),
            poke_score=min(100, poke / count * 10),
            peel_score=min(100, peel / count * 10),
            split_push_score=min(100, split_push / count * 10),
            team_fight_score=min(100, team_fight / count * 10),
            early_game_score=min(100, early_game / count * 10),
            late_game_score=min(100, late_game / count * 10)
        )

    def _find_advantages(self, ally: TeamComposition,
                         enemy: TeamComposition) -> List[str]:
        """找出己方优势"""
        advantages = []

        if ally.engage_score > enemy.engage_score + 15:
            advantages.append("强开团能力领先，可主动发起团战")
        if ally.poke_score > enemy.poke_score + 15:
            advantages.append("Poke消耗能力更强，适合拉扯打法")
        if ally.peel_score > enemy.peel_score + 15:
            advantages.append("保护能力出色，C位生存环境好")
        if ally.team_fight_score > enemy.team_fight_score + 15:
            advantages.append("团战能力占优，正面交锋有优势")
        if ally.early_game_score > enemy.early_game_score + 15:
            advantages.append("前期强势，可积极入侵和争夺资源")
        if ally.late_game_score > enemy.late_game_score + 15:
            advantages.append("后期发力，稳定发育后期更强")

        return advantages

    def _find_disadvantages(self, ally: TeamComposition,
                            enemy: TeamComposition) -> List[str]:
        """找出己方劣势"""
        disadvantages = []

        if ally.engage_score < enemy.engage_score - 15:
            disadvantages.append("开团能力不足，需注意走位")
        if ally.poke_score < enemy.poke_score - 15:
            disadvantages.append("对Poke阵容弱势，避免消耗战")
        if ally.peel_score < enemy.peel_score - 15:
            disadvantages.append("保护能力欠缺，后排需自保")
        if ally.team_fight_score < enemy.team_fight_score - 15:
            disadvantages.append("团战能力偏弱，考虑分推牵制")
        if ally.early_game_score < enemy.early_game_score - 15:
            disadvantages.append("前期偏弱，需稳健发育")
        if ally.late_game_score < enemy.late_game_score - 15:
            disadvantages.append("后期乏力，需前期结束比赛")

        return disadvantages

    def _generate_suggestions(self, ally: TeamComposition,
                              enemy: TeamComposition) -> List[str]:
        """生成战术建议"""
        suggestions = []

        # 根据优劣势生成建议
        if ally.engage_score > enemy.peel_score:
            suggestions.append("建议主动开团，利用开团优势")

        if ally.poke_score > enemy.engage_score:
            suggestions.append("建议拉扯消耗，避免被强开")

        if ally.split_push_score > enemy.team_fight_score:
            suggestions.append("可考虑分推战术，分散敌人注意力")

        if ally.early_game_score > enemy.early_game_score + 20:
            suggestions.append("前期强势，积极入侵野区和争夺河蟹")

        if ally.late_game_score > enemy.late_game_score + 20:
            suggestions.append("后期发力，前期稳健发育")

        if enemy.poke_score > ally.engage_score + 20:
            suggestions.append("敌方Poke强，优先考虑开团机会")

        return suggestions
