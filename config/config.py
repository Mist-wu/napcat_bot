import os
import dotenv
import platform

if platform.system() == "Windows":
    napcat_host = "178.128.61.90"
else:
    napcat_host = "0.0.0.0"

dotenv.load_dotenv()
    
weather_api_key = os.getenv("WEATHER_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
napcat_token = os.getenv("NAPCAT_TOKEN")

root_user = "2550166270"

group_whitelist = set([
    1051660592,
])

user_whitelist = set([
    root_user,
])

user_blacklist = set([
])

def is_user_allowed(user_id: str) -> bool:
    if str(user_id) in user_blacklist:
        return False
    if str(user_id) in user_whitelist:
        return True
    return False

def is_group_allowed(group_id: int) -> bool:
    return int(group_id) in group_whitelist

def is_user_blacklisted(user_id: str) -> bool:
    return str(user_id) in user_blacklist