"""Real-time weather lookup via Open-Meteo (free, no API key required)."""

import requests

_WEATHER_KEYWORD = "날씨"
_NON_CITY_PREFIXES = {"오늘", "현재", "지금", "오늘은", "지금은", ""}

# Open-Meteo's geocoder is indexed by English/romanized place names -- a
# Korean-script query like "서울" returns zero results, and "부산" matches
# several unrelated small villages before the actual city. Translating to
# the English name first finds the right place reliably (verified below).
_CITY_NAME_TO_GEOCODE = {
    "서울": "Seoul", "부산": "Busan", "인천": "Incheon", "대구": "Daegu",
    "대전": "Daejeon", "광주": "Gwangju", "울산": "Ulsan", "수원": "Suwon",
    "제주": "Jeju", "춘천": "Chuncheon", "전주": "Jeonju", "청주": "Cheongju",
    "포항": "Pohang", "창원": "Changwon", "성남": "Seongnam", "고양": "Goyang",
}

# WMO weather codes -> Korean description (https://open-meteo.com/en/docs)
_WEATHER_CODE_KO = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
    45: "옅은 안개", 48: "짙은 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비",
    66: "약한 진눈깨비", 67: "진눈깨비",
    71: "약한 눈", 73: "눈", 75: "강한 눈", 77: "눈날림",
    80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    85: "약한 눈 소나기", 86: "강한 눈 소나기",
    95: "뇌우", 96: "약한 우박을 동반한 뇌우", 99: "강한 우박을 동반한 뇌우",
}


def match_weather(text: str) -> str | None:
    """Return the city to look up weather for, "" to mean "use the default
    city" (no city named, e.g. "오늘 날씨 어때"), or None if `text` isn't a
    weather query at all."""
    if _WEATHER_KEYWORD not in text:
        return None
    prefix = text.split(_WEATHER_KEYWORD, 1)[0].strip(" ,.!?~")
    return "" if prefix in _NON_CITY_PREFIXES else prefix


def get_weather(city: str) -> str:
    """Look up current weather for `city` via Open-Meteo. Never raises --
    returns a Korean apology string on any failure."""
    try:
        geocode_query = _CITY_NAME_TO_GEOCODE.get(city, city)
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": geocode_query, "count": 10, "language": "ko"},
            timeout=5,
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return f"{city}의 날씨 정보를 찾을 수 없습니다."

        # Same-named small villages otherwise often outrank the actual city.
        best = max(results, key=lambda r: r.get("population", 0))
        lat, lon = best["latitude"], best["longitude"]

        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "timezone": "Asia/Seoul",
            },
            timeout=5,
        )
        forecast.raise_for_status()
        current = forecast.json()["current"]
        temp = round(current["temperature_2m"])
        desc = _WEATHER_CODE_KO.get(current["weather_code"], "알 수 없음")

        return f"{city}의 현재 날씨는 {desc}, 기온은 {temp}도입니다."
    except (requests.RequestException, KeyError, ValueError, IndexError) as e:
        print(f"[Weather] 조회 실패: {e}")
        return "죄송합니다, 지금은 날씨 정보를 가져올 수 없어요."
