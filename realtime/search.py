"""Real-time web search via the Tavily API (api_key required, see config.settings).

Tavily's own answer/result text comes back in whatever language the source
pages were in (usually English even for a Korean query), so it's passed
through Jarvis's LLM client for a short Korean summary/translation rather
than spoken as-is. That LLM call is grounded in the search results, not
freeform improvisation, so it doesn't reintroduce the "LLM hallucinates
instead of searching" problem this feature was built to avoid.
"""

import requests

from config.settings import settings

_SEARCH_TRIGGERS = ["검색해줘", "검색해 줘", "찾아줘", "찾아 줘", "알려줘", "알려 줘"]

_SUMMARY_MAX_TOKENS = 60

# Tavily uses 429 for rate limiting, but plan-quota errors have shown up
# under other status codes with "quota"/"rate limit" in the body, so both
# the status code and the body text are checked.
_QUOTA_STATUS_CODES = {429, 432, 433}
_QUOTA_KEYWORDS = ("quota", "rate limit")


def _is_quota_error(response: requests.Response | None) -> bool:
    if response is None:
        return False
    if response.status_code in _QUOTA_STATUS_CODES:
        return True
    try:
        return any(keyword in response.text.lower() for keyword in _QUOTA_KEYWORDS)
    except Exception:
        return False


def match_search(text: str) -> str | None:
    """Return the search query if `text` ends with a search trigger phrase
    and has a non-empty topic before it, else None."""
    stripped = text.strip()
    for trigger in _SEARCH_TRIGGERS:
        if stripped.endswith(trigger):
            topic = stripped[: -len(trigger)].strip(" ,.!?~")
            if topic:
                return topic
    return None


def web_search(query: str, llm) -> str:
    """Search the web for `query` via Tavily, then summarize the result in
    Korean via `llm` (an OllamaClient). Never raises -- returns a Korean
    apology string on any failure, with the reply text varying by failure
    kind (missing key / quota / network / other) so the user knows whether
    it's worth retrying."""
    if not settings.TAVILY_API_KEY:
        print("[Search] API key missing")
        return "검색 기능이 아직 설정되지 않았습니다."

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 5,
            },
            timeout=10,
        )
        if _is_quota_error(response):
            print(f"[Search] Quota exceeded: HTTP {response.status_code}")
            return "이번 달 검색 한도를 모두 사용했습니다. 다음 달에 다시 이용할 수 있습니다."

        response.raise_for_status()
        data = response.json()

        raw = (data.get("answer") or "").strip()
        if not raw:
            results = data.get("results") or []
            if not results:
                return f"{query}에 대한 검색 결과를 찾을 수 없습니다."
            raw = " ".join(r.get("content") or r.get("title", "") for r in results[:3])
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print(f"[Search] Network error: {e}")
        return "검색 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."
    except requests.exceptions.HTTPError as e:
        if _is_quota_error(e.response):
            print(f"[Search] Quota exceeded: {e}")
            return "이번 달 검색 한도를 모두 사용했습니다. 다음 달에 다시 이용할 수 있습니다."
        print(f"[Search] Unexpected error: {e}")
        return "검색 중 문제가 발생했습니다."
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"[Search] Unexpected error: {e}")
        return "검색 중 문제가 발생했습니다."

    return _summarize_ko(query, raw, llm)


def _summarize_ko(query: str, raw: str, llm) -> str:
    prompt = (
        f'아래는 "{query}"에 대한 웹 검색 결과다(영어일 수 있다). '
        "원문을 번역하지 말고, 핵심 내용만 짧은 한국어 문장 2개로 요약해라. "
        "각 문장은 마침표로 끝내고 한 문장에 여러 내용을 이어 붙이지 마라. "
        "총 50자를 넘기지 마라.\n\n"
        f"검색 결과: {raw}"
    )
    try:
        return llm.ask(prompt, max_tokens=_SUMMARY_MAX_TOKENS)
    except Exception as e:
        print(f"[Search] 요약 실패, 검색 결과 원문 반환: {e}")
        return raw
