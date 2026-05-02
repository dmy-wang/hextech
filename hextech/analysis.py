import json
from config import  SUMMONER_SPELL_ID_TO_NAME,CHAMPION_ID_TO_REAL_NAME
class TeamAnalysis:
    def __init__(self):
        self.my_team_bans = []
        self.their_team_bans = []
        self.my_team_picks = []
        self.their_team_picks = []
        self.my_account_id = ""
        self.user_name = ""
        self.my_position = ""
        self.my_teams_id = []
        self.their_teams_id = []
        self.my_teams_skill = {}
        self.their_teams_skill = {}
        self.my_teams_chocies = {}
        self.their_teams_chocies = {}
        self.bp_data = {}
    
    def analyze_user_info(self,data):
        # 分析用户信息，获取账户ID
        self.my_account_id = self.get_accountId(data)

    def get_my_pos(self):
        # 获取我的位置
        return self.my_position
    
    def set_my_pos(self,position):
        # 设置我的位置
        self.my_position = position

    def get_accountId(self,data):
        # 获取账户ID
        return data["accountId"]
    
    def get_bp_data(self):
        self.bp_data["my_position"] = self.my_position
        # 获取BP数据
        return self.bp_data
    
    def update_user_info(self,data):
        # 更新用户信息，获取账户ID和用户名
        self.my_account_id = data["accountId"]
        self.user_name = data["internalName"]

    def update_team_info(self,data):
        my_team_bans = []
        their_team_bans = []
        # 从数据中获取禁用阶段的数据
        # self.my_team_bans = data["bans"]["myTeamBans"]
        # self.their_team_bans = data["bans"]["theirTeamBans"]
        # 遍历第一轮数据，获取禁用英雄
        for action in data["actions"][0]:  # 第一轮是禁用阶段
            if action["type"] == "ban":
                champion_id = action["championId"]
                if champion_id == -1:
                    continue  # 跳过无效的禁用
                champion_name = CHAMPION_ID_TO_REAL_NAME.get(champion_id, f"未知英雄 ({champion_id})")
                ac = action["isAllyAction"]
                if ac:
                    my_team_bans.append(champion_name)
                else:
                    their_team_bans.append(champion_name)
        self.my_team_bans = my_team_bans
        self.their_team_bans = their_team_bans


        my_team_picks = []
        their_team_picks = []
        for player in data["myTeam"]:
            acount_id = player["summonerId"]
            if acount_id == self.my_account_id:
                self.my_position = player["assignedPosition"]
            champion_id = player["championId"]
            champion_name = CHAMPION_ID_TO_REAL_NAME.get(champion_id, f"未知英雄 ({champion_id})")
            position = player["assignedPosition"]
            spell1 = SUMMONER_SPELL_ID_TO_NAME.get(player["spell1Id"], f"未知技能 ({player['spell1Id']})")
            spell2 = SUMMONER_SPELL_ID_TO_NAME.get(player["spell2Id"], f"未知技能 ({player['spell2Id']})")
            #print(f"位置: {position}, 英雄: {champion_name}, 召唤师技能: {spell1} 和 {spell2}")
            if champion_id==0:
                self.my_teams_chocies[position] = champion_name
            else: 
                my_team_picks.append(champion_name)
                self.my_teams_chocies[position] = champion_name
            self.my_teams_skill[position] = (spell1, spell2)
            self.my_teams_skill[position] = (spell1, spell2)


        for player in data["theirTeam"]:
            champion_id = player["championId"]
            champion_name = CHAMPION_ID_TO_REAL_NAME.get(champion_id, f"未知英雄 ({champion_id})")
            position = player["assignedPosition"]
            spell1 = SUMMONER_SPELL_ID_TO_NAME.get(player["spell1Id"], f"未知技能 ({player['spell1Id']})")
            spell2 = SUMMONER_SPELL_ID_TO_NAME.get(player["spell2Id"], f"未知技能 ({player['spell2Id']})")
            #print(f"位置: {position}, 英雄: {champion_name}, 召唤师技能: {spell1} 和 {spell2}")
            if champion_id==0:
                self.their_teams_chocies[position] = champion_name
            else: 
                their_team_picks.append(champion_name)
                self.their_teams_chocies[position] = champion_name
            self.their_teams_skill[position] = (spell1, spell2)
            self.their_teams_skill[position] = (spell1, spell2)

        self.my_team_picks = my_team_picks
        self.their_team_picks = their_team_picks

        # 构造BP数据
        self.bp_data["my_team_bans"] = my_team_bans
        self.bp_data["their_team_bans"] = their_team_bans
        self.bp_data["my_team_picks"] = my_team_picks
        self.bp_data["their_team_picks"] = their_team_picks
        self.bp_data["my_position"] = self.my_position