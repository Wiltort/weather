import requests
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))



def get_coordinates(city_name):
    """
    Получает координаты города по его имени.

    Args:
        city_name: Строка, содержащая название города.

    Returns:
        Словарь с координатами (широта, долгота),
        или None, если город не найден.
    """

    api_key = os.environ.get('GEOLOC_KEY')  # Спрятать нах при пуше!!
    base_url = "https://api.opencagedata.com/geocode/v1/json"

    params = {"q": city_name, "key": api_key}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            coordinates = {
                "latitude": data["results"][0]["geometry"]["lat"],
                "longitude": data["results"][0]["geometry"]["lng"],
            }
            return coordinates
        else:
            return None
    else:
        return None


def get_weather(coordinates):
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "hourly": "temperature_2m",
        "daily": "weather_code",
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_dataframe = pd.DataFrame(data=hourly_data)

    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()

    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        ).strftime("%d.%m.%Y")
    }
    daily_data["weather_code"] = daily_weather_code
    print(daily_weather_code)
    daily_icon = []
    for item in daily_weather_code:
        if item == 0:
            daily_icon.append("01d")
        elif item > 0 and item < 4:
            daily_icon.append("02d")
        elif item == 45 or item == 48:
            daily_icon.append("50d")
        elif item == 51 or item == 53 or item == 55:
            daily_icon.append("09d")
        elif item == 56 or item == 57:
            daily_icon.append("09d")
        elif item == 61 or item == 63 or item == 65 or item == 85 or item == 86:
            daily_icon.append("10d")
        elif item == 66 or item == 67:
            daily_icon.append("10d")
        elif item == 71 or item == 73 or item == 75 or item == 77:
            daily_icon.append("13d")
        elif item == 80 or item == 81 or item == 82:
            daily_icon.append("10d")
        elif item == 95 or item == 96 or item == 99:
            daily_icon.append("11d")
        else:
            daily_icon.append("01d")
    daily_data["weather_icon"] = daily_icon
    daily_dataframe = pd.DataFrame(data=daily_data)
    return hourly_dataframe, daily_dataframe
