# coding:utf-8
"""
LLM BP 推荐服务
使用大语言模型增强 BP 推荐能力
"""
import json
from typing import List, Dict, Optional

from app.common.logger import logger
from app.common.llm_config import LLMClient, llm_client, BP_SYSTEM_PROMPT, BP_BAN_PROMPT_TEMPLATE, BP_PICK_PROMPT_TEMPLATE
from app.ai.recommendation import BanRecommendation, PickRecommendation, Position, RecommendationReason


TAG = "LLMBPService"


class LLMBPService:
    """
    基于 LLM 的 BP 推荐服务
    提供更智能、更人性化的推荐建议
    """

    def __init__(self, client: LLMClient = None):
        self.client = client or llm_client

    async def get_llm_ban_recommendations(
        self,
        ally_picks: List[int],
        enemy_picks: List[int],
        ally_bans: List[int],
        enemy_bans: List[int],
        tier_champions: List[Dict],
        champion_names: Dict[int, str]
    ) -> List[BanRecommendation]:
        """
        使用 LLM 获取 Ban 推荐

        Args:
            ally_picks: 己方已选英雄 ID
            enemy_picks: 敌方已选英雄 ID
            ally_bans: 己方已禁英雄 ID
            enemy_bans: 敌方已禁英雄 ID
            tier_champions: 版本强势英雄列表
            champion_names: 英雄 ID 到名称的映射

        Returns:
            Ban 推荐列表
        """
        try:
            # 构建提示词
            prompt = self._build_ban_prompt(
                ally_picks, enemy_picks, ally_bans, enemy_bans,
                tier_champions, champion_names
            )

            # 调用 LLM
            response = await self.client.chat_with_context(
                user_message=prompt,
                system_prompt=BP_SYSTEM_PROMPT
            )

            # 解析响应
            return self._parse_ban_response(response, champion_names)

        except Exception as e:
            logger.error(f"LLM ban recommendation failed: {e}", TAG)
            return []

    async def get_llm_pick_recommendations(
        self,
        position: Position,
        ally_picks: List[int],
        enemy_picks: List[int],
        ally_bans: List[int],
        enemy_bans: List[int],
        player_masteries: Dict[int, int],
        tier_champions: List[Dict],
        champion_names: Dict[int, str]
    ) -> List[PickRecommendation]:
        """
        使用 LLM 获取 Pick 推荐

        Args:
            position: 需要填充的位置
            ally_picks: 己方已选英雄 ID
            enemy_picks: 敌方已选英雄 ID
            ally_bans: 己方已禁英雄 ID
            enemy_bans: 敌方已禁英雄 ID
            player_masteries: 玩家英雄熟练度
            tier_champions: 版本强势英雄列表
            champion_names: 英雄 ID 到名称的映射

        Returns:
            Pick 推荐列表
        """
        try:
            # 构建提示词
            prompt = self._build_pick_prompt(
                position, ally_picks, enemy_picks, ally_bans, enemy_bans,
                player_masteries, tier_champions, champion_names
            )

            # 调用 LLM
            response = await self.client.chat_with_context(
                user_message=prompt,
                system_prompt=BP_SYSTEM_PROMPT
            )

            # 解析响应
            return self._parse_pick_response(response, position, champion_names)

        except Exception as e:
            logger.error(f"LLM pick recommendation failed: {e}", TAG)
            return []

    def _build_ban_prompt(
        self,
        ally_picks: List[int],
        enemy_picks: List[int],
        ally_bans: List[int],
        enemy_bans: List[int],
        tier_champions: List[Dict],
        champion_names: Dict[int, str]
    ) -> str:
        """构建 Ban 推荐提示词"""
        # 转换英雄 ID 为名称
        ally_names = [champion_names.get(id, str(id)) for id in ally_picks]
        enemy_names = [champion_names.get(id, str(id)) for id in enemy_picks]
        ally_ban_names = [champion_names.get(id, str(id)) for id in ally_bans]
        enemy_ban_names = [champion_names.get(id, str(id)) for id in enemy_bans]

        # 版本强势英雄
        tier_names = []
        for champ in tier_champions[:10]:
            name = champion_names.get(champ.get('championId'), 'Unknown')
            tier = champ.get('tier', 4)
            tier_names.append(f"{name}(T{tier})")

        return BP_BAN_PROMPT_TEMPLATE.format(
            ally_picks=", ".join(ally_names) or "无",
            enemy_picks=", ".join(enemy_names) or "无",
            ally_bans=", ".join(ally_ban_names) or "无",
            enemy_bans=", ".join(enemy_ban_names) or "无",
            tier_champions=", ".join(tier_names)
        )

    def _build_pick_prompt(
        self,
        position: Position,
        ally_picks: List[int],
        enemy_picks: List[int],
        ally_bans: List[int],
        enemy_bans: List[int],
        player_masteries: Dict[int, int],
        tier_champions: List[Dict],
        champion_names: Dict[int, str]
    ) -> str:
        """构建 Pick 推荐提示词"""
        # 转换英雄 ID 为名称
        ally_names = [champion_names.get(id, str(id)) for id in ally_picks]
        enemy_names = [champion_names.get(id, str(id)) for id in enemy_picks]
        ally_ban_names = [champion_names.get(id, str(id)) for id in ally_bans]
        enemy_ban_names = [champion_names.get(id, str(id)) for id in enemy_bans]

        # 玩家擅长英雄
        mastery_items = sorted(player_masteries.items(), key=lambda x: -x[1])[:5]
        mastery_names = [
            f"{champion_names.get(id, str(id))}({score}分)"
            for id, score in mastery_items
        ]

        # 版本强势英雄（该位置）
        tier_names = []
        for champ in tier_champions[:8]:
            name = champion_names.get(champ.get('championId'), 'Unknown')
            tier = champ.get('tier', 4)
            win_rate = champ.get('winRate', 0) * 100
            tier_names.append(f"{name}(T{tier}, {win_rate:.1f}%)")

        position_names = {
            Position.TOP: "上单",
            Position.JUNGLE: "打野",
            Position.MID: "中单",
            Position.ADC: "射手",
            Position.SUPPORT: "辅助"
        }

        return BP_PICK_PROMPT_TEMPLATE.format(
            position=position_names.get(position, position.value),
            ally_picks=", ".join(ally_names) or "无",
            enemy_picks=", ".join(enemy_names) or "无",
            ally_bans=", ".join(ally_ban_names) or "无",
            enemy_bans=", ".join(enemy_ban_names) or "无",
            player_masteries=", ".join(mastery_names) or "暂无数据",
            tier_champions=", ".join(tier_names)
        )

    def _parse_ban_response(
        self,
        response: str,
        champion_names: Dict[int, str]
    ) -> List[BanRecommendation]:
        """
        解析 LLM 的 Ban 推荐响应

        预期格式:
        1. 英雄名称 - 理由
        2. 英雄名称 - 理由
        3. 英雄名称 - 理由
        """
        recommendations = []

        # 创建名称到 ID 的反向映射
        name_to_id = {v: k for k, v in champion_names.items()}

        lines = response.strip().split('\n')
        for line in lines:
            # 尝试解析 "数字. 英雄名称 - 理由" 格式
            if '-' in line:
                parts = line.split('-', 1)
                if len(parts) >= 2:
                    # 提取英雄名称
                    name_part = parts[0].strip()
                    # 移除开头的数字和点
                    if '.' in name_part:
                        name_part = name_part.split('.')[-1].strip()

                    # 查找英雄 ID
                    champion_id = name_to_id.get(name_part)
                    if champion_id:
                        reason = parts[1].strip()
                        recommendations.append(BanRecommendation(
                            champion_id=champion_id,
                            champion_name=name_part,
                            priority=90 - len(recommendations) * 10,  # 递减优先级
                            reasons=[RecommendationReason.BAN_THREAT],
                            threat_score=80
                        ))

        return recommendations[:3]

    def _parse_pick_response(
        self,
        response: str,
        position: Position,
        champion_names: Dict[int, str]
    ) -> List[PickRecommendation]:
        """
        解析 LLM 的 Pick 推荐响应

        预期格式:
        1. 英雄名称 - 理由
        2. 英雄名称 - 理由
        """
        recommendations = []

        # 创建名称到 ID 的反向映射
        name_to_id = {v: k for k, v in champion_names.items()}

        lines = response.strip().split('\n')
        for line in lines:
            if '-' in line:
                parts = line.split('-', 1)
                if len(parts) >= 2:
                    # 提取英雄名称
                    name_part = parts[0].strip()
                    if '.' in name_part:
                        name_part = name_part.split('.')[-1].strip()

                    # 查找英雄 ID
                    champion_id = name_to_id.get(name_part)
                    if champion_id:
                        reason = parts[1].strip()
                        recommendations.append(PickRecommendation(
                            champion_id=champion_id,
                            champion_name=name_part,
                            position=position,
                            priority=90 - len(recommendations) * 10,
                            reasons=[RecommendationReason.TIER_STRONG],
                            tier_score=85,
                            counter_score=75,
                            synergy_score=70,
                            mastery_score=60
                        ))

        return recommendations[:5]


# 全局服务实例
llm_bp_service = LLMBPService()
