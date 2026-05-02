# coding:utf-8
"""
BP 分析器
实时分析 BP 状态并生成推荐
"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass

from .recommendation import (
    Recommendation,
    BanRecommendation,
    PickRecommendation,
    CompositionAnalysis,
    TeamComposition,
    Position,
    RecommendationReason
)
from .champion_evaluator import ChampionEvaluator, EvaluationContext


@dataclass
class BPState:
    """BP 状态"""
    phase: str                         # BAN_PICK1-3, PICK1-3 等
    my_team: List[Dict]                # 己方队伍信息
    their_team: List[Dict]             # 敌方队伍信息
    my_bans: List[int]                 # 己方已禁英雄
    their_bans: List[int]              # 敌方已禁英雄
    my_picks: List[int]                # 己方已选英雄
    their_picks: List[int]             # 敌方已选英雄
    current_action: Optional[Dict]     # 当前行动
    is_my_turn: bool                   # 是否轮到我方


class BPAnalyzer:
    """
    BP 分析器
    监听 BP 状态变化，生成推荐
    """

    def __init__(self, evaluator: ChampionEvaluator = None):
        self.evaluator = evaluator or ChampionEvaluator()
        self.opgg_data: Dict = {}           # OP.GG 数据缓存
        self.summoner_masteries: Dict = {}  # 召唤师熟练度缓存
        self.position_mapping = {
            0: Position.TOP,
            1: Position.JUNGLE,
            2: Position.MID,
            3: Position.ADC,
            4: Position.SUPPORT
        }

    async def set_opgg_data(self, data: Dict):
        """设置 OP.GG 数据"""
        self.opgg_data = data

    async def set_summoner_masteries(self, masteries: Dict[int, int]):
        """设置召唤师熟练度"""
        self.summoner_masteries = masteries

    def parse_bp_state(self, session_data: Dict) -> BPState:
        """解析 BP 会话数据"""
        my_team_id = session_data.get('localPlayerCellId', 0) // 5

        my_team = []
        their_team = []
        my_bans = []
        their_bans = []
        my_picks = []
        their_picks = []

        for team in session_data.get('myTeam', []):
            my_team.append(team)
            if team.get('championId'):
                my_picks.append(team['championId'])

        for team in session_data.get('theirTeam', []):
            their_team.append(team)
            if team.get('championId'):
                their_picks.append(team['championId'])

        for ban in session_data.get('bans', {}).get('myTeamBans', []):
            if ban.get('championId'):
                my_bans.append(ban['championId'])

        for ban in session_data.get('bans', {}).get('theirTeamBans', []):
            if ban.get('championId'):
                their_bans.append(ban['championId'])

        # 判断当前是否轮到我方
        current_action = session_data.get('actions', [[]])[0]
        is_my_turn = False
        current_phase = ""

        if current_action:
            for action in current_action:
                if not action.get('completed', False):
                    actor_cell_id = action.get('actorCellId', -1)
                    is_my_turn = actor_cell_id // 5 == my_team_id
                    current_phase = action.get('type', '')  # "ban" or "pick"
                    break

        return BPState(
            phase=current_phase,
            my_team=my_team,
            their_team=their_team,
            my_bans=my_bans,
            their_bans=their_bans,
            my_picks=my_picks,
            their_picks=their_picks,
            current_action=current_action,
            is_my_turn=is_my_turn
        )

    async def analyze(self, session_data: Dict) -> Recommendation:
        """
        分析 BP 状态，生成推荐

        Args:
            session_data: LCU BP 会话数据

        Returns:
            推荐结果
        """
        state = self.parse_bp_state(session_data)

        # 根据当前阶段生成推荐
        if state.phase == "ban":
            ban_recs = await self._generate_ban_recommendations(state)
            pick_recs = []
        elif state.phase == "pick":
            ban_recs = []
            pick_recs = await self._generate_pick_recommendations(state)
        else:
            ban_recs = await self._generate_ban_recommendations(state)
            pick_recs = await self._generate_pick_recommendations(state)

        # 生成阵容分析
        composition = await self._analyze_composition(state)

        return Recommendation(
            ban_recommendations=ban_recs,
            pick_recommendations=pick_recs,
            composition_analysis=composition,
            current_phase=state.phase,
            current_position=self._get_needed_position(state)
        )

    async def _generate_ban_recommendations(self, state: BPState) -> List[BanRecommendation]:
        """生成 Ban 推荐"""
        recommendations = []

        # 获取版本强势英雄
        tier_list = self.opgg_data.get('tier_list', {})

        # 按位置收集强势英雄
        strong_champions = []
        for position, champions in tier_list.items():
            for champ in champions[:10]:  # 取前10
                if champ['championId'] not in state.my_bans and \
                   champ['championId'] not in state.their_bans:
                    strong_champions.append(champ)

        # 按梯队排序
        strong_champions.sort(key=lambda x: (
            x.get('tier', 5),
            x.get('rank', 999),
            -x.get('winRate', 0)
        ))

        # 生成推荐
        for champ in strong_champions[:5]:
            champion_id = champ['championId']

            # 检查是否威胁己方阵容
            threat_score = await self._calculate_threat_score(champion_id, state)

            reasons = []
            if champ.get('tier', 5) <= 2:
                reasons.append(RecommendationReason.TIER_STRONG)
            if threat_score > 70:
                reasons.append(RecommendationReason.BAN_THREAT)

            # 检查敌方是否有高熟练度
            enemy_mastery = self.summoner_masteries.get(champion_id)

            recommendations.append(BanRecommendation(
                champion_id=champion_id,
                champion_name=champ.get('name', ''),
                priority=100 - champ.get('rank', 50),
                reasons=reasons,
                threat_score=threat_score,
                enemy_mastery=enemy_mastery
            ))

        return recommendations

    async def _generate_pick_recommendations(self, state: BPState) -> List[PickRecommendation]:
        """生成 Pick 推荐"""
        recommendations = []

        # 获取需要填充的位置
        needed_positions = self._get_needed_positions(state)
        if not needed_positions:
            return recommendations

        # 获取可用的强势英雄
        tier_list = self.opgg_data.get('tier_list', {})

        for position in needed_positions:
            position_champs = tier_list.get(position.value, [])

            for champ in position_champs[:15]:
                champion_id = champ['championId']

                # 跳过已选择和已禁用的英雄
                if champion_id in state.my_picks or \
                   champion_id in state.their_picks or \
                   champion_id in state.my_bans or \
                   champion_id in state.their_bans:
                    continue

                # 创建评估上下文
                context = EvaluationContext(
                    champion_id=champion_id,
                    position=position,
                    ally_champions=state.my_picks,
                    enemy_champions=state.their_picks,
                    enemy_bans=state.their_bans,
                    summoner_masteries=self.summoner_masteries,
                    opgg_data=self.opgg_data
                )

                # 执行评估
                scores = await self.evaluator.evaluate(context)

                recommendations.append(PickRecommendation(
                    champion_id=champion_id,
                    champion_name=champ.get('name', ''),
                    position=position,
                    priority=scores['total'],
                    reasons=scores.get('reasons', []),
                    tier_score=scores.get('tier', 0),
                    counter_score=scores.get('counter', 0),
                    synergy_score=scores.get('synergy', 0),
                    mastery_score=scores.get('mastery', 0),
                    win_rate=champ.get('winRate'),
                    pick_rate=champ.get('pickRate')
                ))

        # 按优先级排序
        recommendations.sort(key=lambda x: -x.priority)

        return recommendations[:10]  # 返回前10个推荐

    async def _calculate_threat_score(self, champion_id: int, state: BPState) -> float:
        """计算英雄对己方阵容的威胁程度"""
        # 简化实现：检查是否克制己方已选英雄
        if not self.opgg_data:
            return 50.0

        champion_data = self.opgg_data.get('champion_builds', {}).get(champion_id, {})
        counters = champion_data.get('counters', {})
        strong_against = counters.get('strongAgainst', [])

        threat = 0.0
        for ally_id in state.my_picks:
            for counter in strong_against:
                if counter['championId'] == ally_id:
                    threat += 20 * counter.get('winRate', 0.55)

        return min(100, threat)

    def _get_needed_position(self, state: BPState) -> str:
        """获取当前需要填充的位置"""
        positions = self._get_needed_positions(state)
        return positions[0].value if positions else ""

    def _get_needed_positions(self, state: BPState) -> List[Position]:
        """获取需要填充的位置列表"""
        needed = []

        for cell_id, position in self.position_mapping.items():
            # 检查该位置是否已有英雄
            has_champion = False
            for member in state.my_team:
                if member.get('cellId') == cell_id and member.get('championId'):
                    has_champion = True
                    break

            if not has_champion:
                needed.append(position)

        return needed

    async def _analyze_composition(self, state: BPState) -> Optional[CompositionAnalysis]:
        """分析阵容"""
        if not state.my_picks and not state.their_picks:
            return None

        # TODO: 实现详细的阵容分析
        ally_comp = TeamComposition()
        enemy_comp = TeamComposition()

        return CompositionAnalysis(
            ally_composition=ally_comp,
            enemy_composition=enemy_comp,
            advantages=[],
            disadvantages=[],
            suggestions=[]
        )
