import os
import dotenv
import platform

dotenv.load_dotenv()

if platform.system() == "Windows":
    napcat_host = "178.128.61.90"
else:
    napcat_host = "0.0.0.0"

weather_api_key = os.getenv("WEATHER_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
napcat_token = os.getenv("NAPCAT_TOKEN")

root_user = "2550166270"
jiang_kai_yuan = "3092760442"

# 分别为AI聊天和指令白名单，填入群号
group_ai_whitelist = {1051660592}
group_cmd_whitelist = {1051660592,1025246329}

user_whitelist = {root_user, jiang_kai_yuan}
user_blacklist = set()

def is_user_allowed(user_id: str) -> bool:
    return str(user_id) in user_whitelist and str(user_id) not in user_blacklist

def is_group_ai_allowed(group_id: int) -> bool:
    return int(group_id) in group_ai_whitelist

def is_group_cmd_allowed(group_id: int) -> bool:
    return int(group_id) in group_cmd_whitelist

def is_user_blacklisted(user_id: str) -> bool:
    return str(user_id) in user_blacklist

all = {
    "group_ai_whitelist": group_ai_whitelist,
    "group_cmd_whitelist": group_cmd_whitelist,
    "user_whitelist": user_whitelist,
    "user_blacklist": user_blacklist,
    "root_user": root_user
}