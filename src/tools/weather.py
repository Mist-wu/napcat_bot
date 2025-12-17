import requests
import os
import dotenv
from typing import Dict, Any
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta

dotenv.load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather(city: str) -> dict:
    url = f'https://api2.wer.plus/api/weather?key={API_KEY}'
    response = requests.post(url, data={'city': city})
    return response.json()
 
def get_timezone(lat: float, lon: float) -> ZoneInfo:
    return ZoneInfo("Asia/Shanghai")

def format_weather_info(weather_data: Dict[str, Any]) -> str:
    try:
        data = weather_data.get('data', {})
        weather = data.get('weather', {})
        location = weather.get('location', {})
        current = weather.get('current', {})
        forecast = data.get('forecast', [])
        air_quality = weather.get('air_quality', {})
        wind = current.get('wind', {})
        lat = float(location.get("coordinates", {}).get("lat", 0))
        lon = float(location.get("coordinates", {}).get("lon", 0))

        def get_weather_emoji(condition: str) -> str:
            weather_emojis = {
                '晴朗': '☀️', '晴': '☀️', '多云': '⛅', '阴': '☁️',
                '小雨': '🌧️', '中雨': '🌧️', '大雨': '⛈️', '暴雨': '🌊',
                '雷阵雨': '⛈️', '雨': '🌧️', '阵雨': '🌦️',
                '小雪': '🌨️', '中雪': '❄️', '大雪': '❄️', '暴雪': '☃️', '雪': '❄️',
                '雨夹雪': '🌨️', '雾': '🌫️', '霾': '😷', '沙尘': '🏜️',
            }
            for key, emoji in weather_emojis.items():
                if key in condition:
                    return emoji
            return '🌤️'

        def get_temp_emoji(temp: int) -> str:
            if temp >= 35:
                return '🥵'
            elif temp >= 25:
                return '😎'
            elif temp >= 15:
                return '😊'
            elif temp >= 5:
                return '🧥'
            elif temp >= -5:
                return '🥶'
            else:
                return '🧊'

        def get_wind_emoji(speed: str) -> str:
            import re
            match = re.search(r'(\d+)', speed)
            if match:
                level = int(match.group(1))
                if level <= 2:
                    return '🍃'
                elif level <= 4:
                    return '🌬️'
                elif level <= 6:
                    return '💨'
                else:
                    return '🌪️'
            return '🍃'

        def get_aqi_emoji(aqi: int) -> str:
            if aqi <= 50:
                return '🟢 优'
            elif aqi <= 100:
                return '🟡 良'
            elif aqi <= 150:
                return '🟠 轻度污染'
            elif aqi <= 200:
                return '🔴 中度污染'
            else:
                return '🟣 重度污染'

        city_name = location.get('name', '未知')
        state = location.get('state', '')
        condition = current.get('condition', '未知')
        temp = current.get('temperature', 0)
        feels_like = current.get('feels_like', 0)
        humidity = current.get('humidity', 0)
        wind_dir = wind.get('direction', '未知')
        wind_speed = wind.get('speed', '未知')
        aqi = air_quality.get('aqi', 0)

        output = f"""
🌍 {state} · {city_name.upper()}

{get_weather_emoji(condition)} 当前天气: {condition}
{get_temp_emoji(temp)} 温度: {temp}°C (体感 {feels_like}°C)
{get_wind_emoji(wind_speed)} 风况: {wind_dir} {wind_speed}
💧 湿度: {humidity}%
🌬️ 空气质量: AQI {aqi} {get_aqi_emoji(aqi)}

📅 未来天气预报:
"""

        for day in forecast:
            date = day.get('date', '')
            high = day.get('high_temp', 0)
            low = day.get('low_temp', 0)
            output += f"  {date}: {get_temp_emoji(high)} {low}°C ~ {high}°C\n"

        last_updated = weather.get('metadata', {}).get('last_updated', '未知')
        if last_updated and last_updated != '未知':
            try:
                dt_utc = datetime.fromisoformat(last_updated.replace("Z", "+00:00")).astimezone(timezone.utc)
                zone = get_timezone(lat, lon)
                dt_local = dt_utc.astimezone(zone)
                time_str = dt_local.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                time_str = last_updated[:16].replace('T', ' ')
        else:
            time_str = "未知"
        output += "\n🕐 数据更新于: " + time_str

        return output.strip()
    except Exception as e:
        return f"❌ 天气信息解析失败: {str(e)}"