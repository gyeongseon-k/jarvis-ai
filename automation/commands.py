"""Local automation: detects action commands in text and runs the matching Windows program."""

import subprocess
from datetime import datetime

_WEEKDAYS_KO = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

COMMANDS = {
    "open_chrome": {
        "keywords": ["크롬 열어", "브라우저 열어"],
        "target": "chrome",
        "found_reply": "크롬을 실행합니다.",
        "not_found_reply": "크롬을 찾을 수 없습니다.",
    },
    "open_calculator": {
        "keywords": ["계산기 열어"],
        "target": "calc",
        "found_reply": "계산기를 실행합니다.",
        "not_found_reply": "계산기를 찾을 수 없습니다.",
    },
    "open_notepad": {
        "keywords": ["메모장 열어"],
        "target": "notepad",
        "found_reply": "메모장을 실행합니다.",
        "not_found_reply": "메모장을 찾을 수 없습니다.",
    },
    "open_explorer": {
        "keywords": ["탐색기 열어"],
        "target": "explorer",
        "found_reply": "탐색기를 실행합니다.",
        "not_found_reply": "탐색기를 찾을 수 없습니다.",
    },
    "open_taskmgr": {
        "keywords": ["작업 관리자 열어", "작업관리자 열어"],
        "target": "taskmgr",
        "found_reply": "작업 관리자를 실행합니다.",
        "not_found_reply": "작업 관리자를 찾을 수 없습니다.",
    },
    "open_settings": {
        "keywords": ["설정 열어"],
        "target": "ms-settings:",
        "found_reply": "설정을 실행합니다.",
        "not_found_reply": "설정을 찾을 수 없습니다.",
    },
    "open_vscode": {
        "keywords": ["vs code 열어", "비주얼 스튜디오 코드 열어", "코드 열어"],
        "target": "code",
        "found_reply": "VS Code를 실행합니다.",
        "not_found_reply": "VS Code를 찾을 수 없습니다.",
    },
    "open_terminal": {
        "keywords": ["터미널 열어"],
        "target": "wt",
        "found_reply": "터미널을 실행합니다.",
        "not_found_reply": "터미널을 찾을 수 없습니다.",
    },
    "open_discord": {
        "keywords": ["디스코드 열어"],
        "target": "discord",
        "found_reply": "디스코드를 실행합니다.",
        "not_found_reply": "디스코드를 찾을 수 없습니다.",
    },
    "open_kakaotalk": {
        "keywords": ["카카오톡 열어"],
        "target": "kakaotalk",
        "found_reply": "카카오톡을 실행합니다.",
        "not_found_reply": "카카오톡을 찾을 수 없습니다.",
    },
    "tell_time": {
        "keywords": ["오늘 몇 시야", "지금 몇 시야", "현재 시간 알려줘", "시간 알려줘"],
    },
    "tell_date": {
        "keywords": ["오늘 날짜는", "오늘 며칠이야", "현재 날짜 알려줘", "오늘 무슨 요일이야"],
    },
}


def match_command(text: str) -> str | None:
    """Return the matching command name for `text`, or None if it isn't a command.

    Picks the longest matching keyword rather than the first one in
    COMMANDS, since some keywords are substrings of others once spaces are
    stripped (e.g. "코드 열어" for VS Code is contained in "디스코드 열어") --
    the longer, more specific match wins regardless of dict order."""
    normalized = text.replace(" ", "").lower()
    best_name = None
    best_len = 0
    for name, spec in COMMANDS.items():
        for keyword in spec["keywords"]:
            normalized_keyword = keyword.replace(" ", "").lower()
            if normalized_keyword in normalized and len(normalized_keyword) > best_len:
                best_name = name
                best_len = len(normalized_keyword)
    return best_name


class CommandRunner:
    def __init__(self):
        self.handlers = {
            name: self._make_opener(spec["target"], spec["found_reply"], spec["not_found_reply"])
            for name, spec in COMMANDS.items()
            if "target" in spec
        }
        self.handlers["tell_time"] = self.tell_time
        self.handlers["tell_date"] = self.tell_date

    def run(self, command_name: str) -> str:
        """Execute `command_name` and return the reply text to speak."""
        return self.handlers[command_name]()

    def _make_opener(self, target: str, found_reply: str, not_found_reply: str):
        def opener() -> str:
            return self._start_process(target, found_reply, not_found_reply)

        return opener

    def _start_process(self, target: str, found_reply: str, not_found_reply: str) -> str:
        """Launch `target` via PowerShell's Start-Process and reply based on
        whether it actually launched. Start-Process exits non-zero (and
        writes an error) when it can't resolve `target` to a program, which
        is the only signal we have -- it only checks Windows' PATH/App
        Paths/registered URI schemes, not every possible install location,
        so an installed-but-not-on-PATH app can still come back as "not
        found"."""
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", f"Start-Process '{target}'"],
                capture_output=True,
                text=True,
                errors="replace",  # PowerShell's error stream isn't always UTF-8
                timeout=15,
            )
        except (subprocess.SubprocessError, OSError) as e:
            print(f"[Command] '{target}' 실행 중 오류: {e}")
            return not_found_reply

        if result.returncode != 0:
            print(f"[Command] '{target}' 실행 실패 (code={result.returncode}): {result.stderr.strip()}")
            return not_found_reply
        return found_reply

    def tell_time(self) -> str:
        now = datetime.now()
        period = "오전" if now.hour < 12 else "오후"
        hour_12 = now.hour % 12 or 12
        return f"현재 시간은 {period} {hour_12}시 {now.minute}분입니다."

    def tell_date(self) -> str:
        now = datetime.now()
        weekday = _WEEKDAYS_KO[now.weekday()]
        return f"오늘은 {now.year}년 {now.month}월 {now.day}일 {weekday}입니다."
