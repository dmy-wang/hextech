# coding:utf-8
"""
召唤师分析器
分析召唤师的历史数据、英雄池、游戏风格
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import Counter


@dataclass
class ChampionMastery:
    """英雄熟练度"""
    champion_id: int
    champion_name: str
    level: int
    points: int
    last_play_time: int
    chest_granted: bool


@dataclass
class RankInfo:
    """段位信息"""
    queue_type: str
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int
    win_rate: float


@dataclass
class PlayStyle:
    """游戏风格"""
    aggression: float           # 激进程度 0-100
    vision_focus: float         # 视野重视程度
    team_fight_focus: float     # 团战参与度
    split_push_tendency: float  # 分推倾向
    roam_tendency: float        # 游走倾向


class SummonerAnalyzer:
    """
    召唤师分析器
    分析召唤师的各项数据
    """

    def __init__(self, connector):
        """
        Args:
            connector: LCU connector 实例
        """
        self.connector = connector

    async def analyze(self, puuid: str) -> Dict:
        """
        分析召唤师

        Args:
            puuid: 召唤师 PUUID

        Returns:
            分析结果
        """
        # 获取基础信息
        summoner = await self.connector.getSummonerByPuuid(puuid)

        # 获取英雄熟练度
        masteries = await self._get_champion_masteries(summoner['id'])

        # 获取段位信息
        ranks = await self._get_rank_info(puuid)

        # 获取最近战绩
        recent_matches = await self._get_recent_matches(puuid)

        # 分析位置偏好
        position_pref = self._analyze_position_preference(recent_matches)

        # 分析游戏风格
        play_style = self._analyze_play_style(recent_matches)

        # 预测可能选择的位置
        predicted_position = self._predict_position(position_pref, ranks)

        return {
            'summoner': summoner,
            'masteries': masteries,
            'ranks': ranks,
            'position_preference': position_pref,
            'play_style': play_style,
            'predicted_position': predicted_position,
            'threat_level': self._calculate_threat_level(masteries, ranks)
        }

    async def _get_champion_masteries(self, summoner_id: str) -> List[ChampionMastery]:
        """获取英雄熟练度"""
        try:
            data = await self.connector.getChampionMasteries(summoner_id)

            masteries = []
            for item in data[:10]:  # 取前10
                masteries.append(ChampionMastery(
                    champion_id=item['championId'],
                    champion_name=self.connector.manager.getChampionNameById(
                        item['championId']),
                    level=item['championLevel'],
                    points=item['championPoints'],
                    last_play_time=item['lastPlayTime'],
                    chest_granted=item.get('chestGranted', False)
                ))

            return masteries
        except Exception:
            return []

    async def _get_rank_info(self, puuid: str) -> List[RankInfo]:
        """获取段位信息"""
        try:
            data = await self.connector.getRankedStats(puuid)

            ranks = []
            for item in data.get('queueMap', {}).values():
                if item.get('division'):  # 有段位
                    wins = item.get('wins', 0)
                    losses = item.get('losses', 0)
                    total = wins + losses

                    ranks.append(RankInfo(
                        queue_type=item.get('queueType', ''),
                        tier=item.get('tier', ''),
                        rank=item.get('division', ''),
                        league_points=item.get('leaguePoints', 0),
                        wins=wins,
                        losses=losses,
                        win_rate=wins / total if total > 0 else 0
                    ))

            return ranks
        except Exception:
            return []

    async def _get_recent_matches(self, puuid: str, count: int = 20) -> List[Dict]:
        """获取最近战绩"""
        try:
            # 使用 SGP 接口获取战绩
            matches = await self.connector.getMatchIdsByPuuid(
                puuid, begIndex=0, endIndex=count)

            detailed_matches = []
            for match_id in matches[:count]:
                try:
                    detail = await self.connector.getMatchDetail(match_id)
                    detailed_matches.append(detail)
                except Exception:
                    continue

            return detailed_matches
        except Exception:
            return []

    def _analyze_position_preference(self, matches: List[Dict]) -> Dict[str, float]:
        """分析位置偏好"""
        if not matches:
            return {
                'TOP': 0.2,
                'JUNGLE': 0.2,
                'MID': 0.2,
                'ADC': 0.2,
                'SUPPORT': 0.2
            }

        position_counts = Counter()

        for match in matches:
            # 从比赛数据中提取位置信息
            for participant in match.get('info', {}).get('participants', []):
                # TODO: 根据 puuid 匹配当前召唤师
                position = participant.get('teamPosition', 'UNKNOWN')
                if position in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']:
                    position_counts[position] += 1

        total = sum(position_counts.values()) or 1

        return {
            'TOP': position_counts.get('TOP', 0) / total,
            'JUNGLE': position_counts.get('JUNGLE', 0) / total,
            'MID': position_counts.get('MIDDLE', 0) / total,
            'ADC': position_counts.get('BOTTOM', 0) / total,
            'SUPPORT': position_counts.get('UTILITY', 0) / total
        }

    def _analyze_play_style(self, matches: List[Dict]) -> PlayStyle:
        """分析游戏风格"""
        if not matches:
            return PlayStyle(
                aggression=50.0,
                vision_focus=50.0,
                team_fight_focus=50.0,
                split_push_tendency=50.0,
                roam_tendency=50.0
            )

        # TODO: 基于比赛数据计算游戏风格指标
        # 击杀参与率 -> team_fight_focus
        # 眼位数据 -> vision_focus
        # 分推数据 -> split_push_tendency

        return PlayStyle(
            aggression=50.0,
            vision_focus=50.0,
            team_fight_focus=50.0,
            split_push_tendency=50.0,
            roam_tendency=50.0
        )

    def _predict_position(self, position_pref: Dict[str, float],
                          ranks: List[RankInfo]) -> str:
        """预测可能选择的位置"""
        # 取偏好最高的位置
        max_position = max(position_pref.items(), key=lambda x: x[1])
        return max_position[0]

    def _calculate_threat_level(self, masteries: List[ChampionMastery],
                                ranks: List[RankInfo]) -> float:
        """计算威胁等级"""
        # 基于段位和熟练度计算
        rank_score = 50.0

        for rank in ranks:
            if rank.queue_type in ['RANKED_SOLO_5x5', 'RANKED_FLEX_SR']:
                tier_scores = {
                    'IRON': 10, 'BRONZE': 20, 'SILVER': 30,
                    'GOLD': 40, 'PLATINUM': 55, 'EMERALD': 65,
                    'DIAMOND': 75, 'MASTER': 85, 'GRANDMASTER': 90,
                    'CHALLENGER': 100
                }
                rank_score = max(rank_score,
                                 tier_scores.get(rank.tier, 50))

        # 熟练度加成
        mastery_bonus = 0.0
        if masteries:
            top_mastery = masteries[0]
            if top_mastery.points > 100000:
                mastery_bonus = 10.0

        return min(100, rank_score + mastery_bonus)
