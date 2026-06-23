"""Local automation: detects action commands in text and runs the matching Windows program."""

import subprocess

COMMANDS = {
    "open_chrome": {
        "keywords": ["크롬 열어", "브라우저 열어"],
        "reply": "크롬을 실행합니다.",
    },
    "open_vscode": {
        "keywords": ["vs code 열어", "비주얼 스튜디오 코드 열어"],
        "reply": "VS Code를 실행합니다.",
    },
}


def match_command(text: str) -> str | None:
    """Return the matching command name for `text`, or None if it isn't a command."""
    normalized = text.replace(" ", "").lower()
    for name, spec in COMMANDS.items():
        for keyword in spec["keywords"]:
            if keyword.replace(" ", "").lower() in normalized:
                return name
    return None


class CommandRunner:
    def __init__(self):
        self.handlers = {
            "open_chrome": self.open_chrome,
            "open_vscode": self.open_vscode,
        }

    def run(self, command_name: str) -> str:
        """Execute `command_name` and return the reply text to speak."""
        self.handlers[command_name]()
        return COMMANDS[command_name]["reply"]

    def open_chrome(self) -> None:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Start-Process chrome"], check=False
        )

    def open_vscode(self) -> None:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Start-Process code"], check=False
        )
