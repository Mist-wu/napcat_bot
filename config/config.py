import os
import dotenv

dotenv.load_dotenv()

weather_api_key = os.getenv("WEATHER_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

root_user = "2550166270"