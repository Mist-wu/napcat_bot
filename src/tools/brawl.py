import requests

def get_club_info(club_tag):
    url = f"https://api.brawlstars.top/api/club/{club_tag}"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        club_dict = r.json()
        if club_dict.get("success"):
            return format_club_info(club_dict)
    except Exception as e:
        return f"请求出错：{e}"

def format_club_info(club_dict):
    club = club_dict['query']
    type_map = {1: "自由加入", 2: "需要批准", 3: "不可加入"}
    role_map = {1: "队员", 3: "资深队员", 4: "副队长", 2: "队长"}

    text = (
        f"🏆 俱乐部信息\n"
        f"名称：{club.get('name', '')}\n"
        f"标签：{club.get('tag', '')}\n"
        f"类型：{type_map.get(club.get('type',0),'未知')}\n"
        f"成员人数：{club.get('memberCount',0)}/{len(club.get('members',[]))}\n"
        f"总奖杯数：{club.get('totalTrophies',0)}\n"
        f"入会奖杯要求：{club.get('requiredTrophies',0)}\n"
        f"在线人数：{club.get('onlineCount',0)}\n"
        f"简介：{club.get('description','')}\n"
        f"------\n"
        f"成员列表：\n"
    )
    for i, m in enumerate(club.get("members", []), 1):
        name = m.get('name', '')
        tag = m.get('tag', '')
        trophies = m.get('trophies', 0)
        role = role_map.get(m.get('role', 0), "未知")
        text += (
            f"{i}. {name}（{tag}） | 奖杯:{trophies} |  职位:{role}\n"
        )
    return text

def get_player_info(player_tag):
    url = f"https://api.brawlstars.top/api/player/{player_tag}"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        player_dict = r.json()
        if player_dict.get("success"):
            return format_player_info(player_dict)
    except Exception as e:
        return f"请求出错：{e}"

def format_player_info(player_dict):
    player = player_dict['query']
    name = player.get('name', '')
    total_trophies = player.get('data', {}).get('trophiesInfo', {}).get('totalTrophies', 0)
    brawlpass = '已购买' if player.get('brawlpass', False) else '未购买'
    club_tag = player.get('club', {}).get('tag', '')
    year = player.get('registerInfo', {}).get('year', '')
    single_win = int(player.get('data', {}).get('profile', {}).get('single', 0)) - int(player.get('data', {}).get('profile', {}).get('double', 0))
    double_win = player.get('data', {}).get('profile', {}).get('double', 0)
    group_win = player.get('data', {}).get('profile', {}).get('group', 0)

    text = (
        f"昵称：{name}\n"
        f"总奖杯数：{total_trophies}\n"
        f"是否购买通行证：{brawlpass}\n"
        f"战队标签：{club_tag}\n"
        f"注册年份：{year}\n"
        f"3v3模式胜场：{group_win}\n"
        f"单人模式胜场：{single_win}\n"
        f"双人模式胜场：{double_win}"
    )
    return text

if __name__ == "__main__":
    tag = input("请输入玩家tag：").strip().upper()
    print(get_player_info(tag))
