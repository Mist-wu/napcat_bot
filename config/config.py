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