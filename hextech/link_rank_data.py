import requests
import time

# 步骤1：获取英雄ID映射
herolist_url = "https://pvp.qq.com/web201605/js/herolist.json"
response = requests.get(herolist_url)
hero_data = response.json()
hero_id_map = {str(hero['ename']): hero['cname'] for hero in hero_data}

# 步骤2：遍历每个英雄ID
headers = {'User-Agent': 'Mozilla/5.0...'}

for hero_id in hero_id_map.keys():
    try:
        matchup_data = get_matchup_data(hero_id)
        top3_win, top3_lose = process_matchup(matchup_data, hero_id_map)
        print(f"英雄 {hero_id_map[hero_id]} 的对位数据：")
        print("胜率前三：", top3_win)
        print("败率前三：", top3_lose)
        time.sleep(1)  # 控制频率
    except Exception as e:
        print(f"获取英雄 {hero_id} 数据失败：{e}")