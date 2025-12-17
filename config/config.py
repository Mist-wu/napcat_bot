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

# 群聊白名单：允许bot工作的群号
group_whitelist = [
    1051660592,
]

# 用户白名单：允许私聊唤醒bot的用户
user_whitelist = [
    root_user,
]

# 用户黑名单：无论群聊还是私聊，禁止bot回复这些用户
user_blacklist = [
]