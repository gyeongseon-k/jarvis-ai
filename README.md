# Jarvis AI Assistant

웨이크 워드("자비스")로 호출해 음성으로 대화하고, 음성 명령으로 로컬 프로그램을 실행하는 개인용 AI 어시스턴트입니다. 음성 인식·LLM 응답·음성 합성·자동화까지 전 과정을 로컬/온프레미스로 처리합니다(클라우드 LLM API 비용 없음).

Windows 11 + WSL2(Ubuntu) 환경을 기준으로 만들어졌으며, WSLg의 PulseAudio 오디오 브리지와 PowerShell 상호운용을 활용해 WSL 안에서 마이크 입력과 Windows 프로그램 실행을 모두 처리합니다.

## 주요 기능

- **웨이크 워드 호출**: "자비스"라고 부르기 전에는 어떤 발화도 처리하지 않음 (상태 머신: `IDLE` ↔ `LISTENING`)
- **음성 인식(STT)**: `faster-whisper`로 한국어 음성을 로컬에서 텍스트로 변환
- **로컬 LLM 응답**: Ollama로 구동되는 `qwen2.5:3b`가 일반 대화에 응답
- **음성 합성(TTS)**: Windows 내장 음성(System.Speech)으로 응답을 읽어줌
- **로컬 자동화**: "크롬 열어", "VS Code 열어" 같은 명령은 LLM을 거치지 않고 즉시 실행

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 음성 캡처 | `parec` (PulseAudio, WSLg 오디오 브리지) |
| STT | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CPU, int8) |
| LLM | [Ollama](https://ollama.com/) + `qwen2.5:3b` (HTTP API, `localhost:11434`) |
| TTS | Windows `System.Speech.Synthesis` (PowerShell 호출), 실패 시 `pyttsx3` 폴백 |
| 자동화 | Python `subprocess` + PowerShell `Start-Process` |
| 설정 | `python-dotenv` (`.env`) |
| 언어/런타임 | Python 3.12, WSL2 (Ubuntu) on Windows 11 |

## 프로젝트 구조

```
Jarvis-AI/
├── voice_recognition/
│   ├── recorder.py      # parec로 마이크 녹음 (WAV)
│   ├── listener.py      # 녹음 + faster-whisper 전사
│   └── wake_word.py     # 웨이크 워드("자비스") 감지
├── llm/
│   └── ollama_client.py # Ollama HTTP API 클라이언트
├── tts/
│   └── speaker.py        # Windows TTS(PowerShell) / pyttsx3 폴백
├── automation/
│   └── commands.py       # 명령어 분류 + 로컬 프로그램 실행
├── config/
│   └── settings.py       # .env 기반 설정
├── assistant.py            # 웨이크 워드 상태 머신 (IDLE/LISTENING)
├── main.py                  # 실행 진입점
├── requirements.txt
└── .env                      # (직접 생성, git에는 포함 안 됨)
```

## 설치 방법

### 1. 시스템 패키지 (WSL 내부)

마이크 캡처에는 `parec`(PulseAudio 클라이언트)이 필요합니다. WSLg가 기본 제공하는 PulseAudio 브리지를 그대로 사용하므로 PyAudio/portaudio 빌드는 필요 없습니다.

```bash
sudo apt update
sudo apt install -y pulseaudio-utils python3.12-venv
```

### 2. Python 가상환경

```bash
git clone <repo-url>
cd Jarvis-AI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 환경변수

루트에 `.env` 파일을 생성합니다.

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
VOICE_LANGUAGE=ko
RECORD_SECONDS=5
```

## Ollama 설정 방법

1. Windows에 [Ollama](https://ollama.com/download)를 설치합니다 (WSL 안이 아니라 Windows 호스트에 설치 — 기본 포트 `11434`가 WSL에서도 `localhost`로 접근 가능).
2. 모델을 받습니다.
   ```bash
   ollama pull qwen2.5:3b
   ```
3. 서버가 떠 있는지 확인합니다.
   ```bash
   curl http://localhost:11434/api/tags
   ```
   `qwen2.5:3b`가 목록에 보이면 정상입니다. 다른 모델을 쓰려면 `.env`의 `OLLAMA_MODEL`만 바꾸면 됩니다.

## 실행 방법

```bash
source .venv/bin/activate
python main.py
```

실행하면 시작 음성 테스트("자비스 음성 출력 테스트입니다.")가 재생되고, 이후 `자비스`라는 호출을 기다리는 대기(`IDLE`) 상태가 됩니다. `Ctrl+C`로 종료합니다.

## 사용 예시

**일반 대화 (Qwen 응답)**

```
사용자: "자비스"
Jarvis: "네, 말씀하세요."
사용자: "오늘 날씨 어때"
Jarvis: (Qwen이 생성한 응답을 음성으로 출력)
```

**로컬 자동화 명령**

```
사용자: "자비스"
Jarvis: "네, 말씀하세요."
사용자: "VS Code 열어"
Jarvis: "VS Code를 실행합니다."
→ Windows에서 VS Code 실행
```

지원 명령어: `크롬 열어` / `브라우저 열어` → Chrome 실행, `VS Code 열어` / `비주얼 스튜디오 코드 열어` → VS Code 실행. 그 외 모든 발화는 Qwen으로 전달됩니다.

명령 처리가 끝나면 자동으로 대기(`IDLE`) 상태로 돌아가며, 다시 "자비스"라고 불러야 다음 명령을 받습니다.

## 향후 계획

- [ ] 웨이크 워드 다중 지원 ("헤이 자비스" 등 변형 인식)
- [ ] 자동화 명령 확장 (파일 검색, 창 전환, 시스템 제어 등)
- [ ] 대화 컨텍스트 유지 (멀티턴 대화 메모리)
- [ ] STT 모델 크기/정확도 옵션화 (`tiny`~`large` 선택 가능하게)
- [ ] 응답 스트리밍 적용 검토 (현재는 비스트리밍 MVP)
- [ ] 에러/재시도 처리 강화 (Ollama 다운, 마이크 장치 끊김 등)
- [ ] 패키징 및 자동 시작(Windows 시작 시 백그라운드 실행) 지원
