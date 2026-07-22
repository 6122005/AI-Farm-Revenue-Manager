import os
import httpx
from datetime import datetime
from typing import Dict, Any
from app.config import OPENWEATHER_API_KEY, OPENWEATHER_CITY

class WeatherService:
    def __init__(self, api_key: str = None, city: str = None):
        self.api_key = api_key or OPENWEATHER_API_KEY
        self.city = city or OPENWEATHER_CITY or "Lonavala"

    def get_forecast(self, booking_date_str: str) -> Dict[str, Any]:
        """
        Fetches live OpenWeather API forecast ONLY if target booking date is within 5 days from today.
        Otherwise provides realistic seasonal weather forecast for the specific target month.
        """
        try:
            target_dt = datetime.strptime(booking_date_str.split()[0], "%Y-%m-%d")
            today_dt = datetime.now()
            days_diff = (target_dt.date() - today_dt.date()).days

            # Only use OpenWeather live 5-day forecast API if target date is within [0, 5] days from today!
            if 0 <= days_diff <= 5 and self.api_key and self.api_key.strip():
                url = f"https://api.openweathermap.org/data/2.5/forecast?q={self.city}&appid={self.api_key}&units=metric"
                response = httpx.get(url, timeout=4.0)
                if response.status_code == 200:
                    data = response.json()
                    best_match = None
                    min_diff = float("inf")
                    
                    for item in data.get("list", []):
                        item_dt = datetime.fromtimestamp(item["dt"])
                        diff = abs((item_dt.date() - target_dt.date()).total_seconds())
                        if diff < min_diff:
                            min_diff = diff
                            best_match = item
                            
                    if best_match:
                        main = best_match.get("main", {})
                        weather_arr = best_match.get("weather", [{}])
                        wind = best_match.get("wind", {})
                        clouds = best_match.get("clouds", {})
                        pop = best_match.get("pop", 0.0) * 100
                        
                        return {
                            "temperature": round(main.get("temp", 26.0), 1),
                            "rain_probability": round(pop, 1),
                            "humidity": round(main.get("humidity", 65.0), 1),
                            "wind_speed": round(wind.get("speed", 3.5), 1),
                            "cloud_cover": round(float(clouds.get("all", 20.0)), 1),
                            "condition": weather_arr[0].get("main", "Clear"),
                            "source": f"OpenWeather API (Live Day +{days_diff})"
                        }
        except Exception as e:
            print(f"⚠️ Live weather API skipped: {e}")

        return self._generate_seasonal_fallback(booking_date_str)

    def _generate_seasonal_fallback(self, booking_date_str: str) -> Dict[str, Any]:
        try:
            dt = datetime.strptime(booking_date_str, "%Y-%m-%d")
            month = dt.month
        except Exception:
            month = 7

        if 6 <= month <= 9:
            temp = 24.5 + (month % 3) * 1.2
            rain_prob = 75.0 if month in [7, 8] else 50.0
            humidity = 85.0
            cloud_cover = 80.0 if month in [7, 8] else 60.0
            condition = "Heavy Rain" if month in [7, 8] else "Moderate Rain"
        elif month in [11, 12, 1, 2]:
            temp = 21.0 + (month % 2) * 2.0
            rain_prob = 5.0
            humidity = 45.0
            cloud_cover = 15.0
            condition = "Pleasant / Clear"
        elif 3 <= month <= 5:
            temp = 32.0 + (month - 3) * 2.5
            rain_prob = 10.0
            humidity = 55.0
            cloud_cover = 10.0
            condition = "Sunny / Warm"
        else:
            temp = 27.5
            rain_prob = 20.0
            humidity = 60.0
            cloud_cover = 25.0
            condition = "Clear Sky"

        return {
            "temperature": round(temp, 1),
            "rain_probability": round(rain_prob, 1),
            "humidity": round(humidity, 1),
            "wind_speed": 4.2,
            "cloud_cover": round(cloud_cover, 1),
            "condition": condition,
            "source": "Seasonal Weather Model (Fallback)"
        }

weather_service = WeatherService()
