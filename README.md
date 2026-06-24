# Jarvis AI Assistant

웨이크워드("자비스")로 부르면 음성으로 대화하고, 실시간 시간·날짜·날씨·웹 검색에 답하고, 음성 명령으로 로컬 프로그램을 실행하는 개인용 AI 음성 비서입니다. 음성 인식·LLM 응답·음성 합성·자동화까지 전 과정을 로컬 LLM(Ollama) 기반으로 처리하며, 시간/날짜/날씨/검색처럼 실시간성이 필요한 질문은 LLM을 거치지 않고 직접 조회해 더 빠르고 정확하게 답합니다.

Windows 11 + WSL2(Ubuntu) 환경을 기준으로 만들어졌으며, WSLg의 PulseAudio 오디오 브리지로 마이크 입력과 스피커 출력을 모두 WSL 안에서 처리하고, PowerShell 상호운용으로 Windows 프로그램을 실행합니다.

## 구현 완료 기능

- **웨이크워드 호출 (fuzzy matching)**: "자비스"로 부르기 전엔 어떤 발화도 처리하지 않음. Whisper 오인식 변형(`자비스`, `사비스`, `자빗스`, `자비스스`, `자비스요`)을 음절 위치별 허용 문자 집합으로 인식하면서, 무관한 일반 대화("자비를 구하다", "비스킷" 등)는 오탐하지 않도록 설계
- **웨이크워드+명령 즉시 처리**: "자비스 안녕" / "자비스 오늘 몇 시야" / "자비스 크롬 열어"처럼 한 호흡에 명령까지 말하면 확인 응답 없이 바로 실행. "자비스"만 단독으로 말하면 "옛썰, 말씀하세요."로 응답하고 다음 발화를 기다리는 2단계 방식도 유지
- **음성 인식(STT)**: `faster-whisper`로 한국어 음성을 로컬에서 텍스트로 변환. 고정 시간 녹음이 아니라 무음 감지(VAD)로 발화가 끝나면 즉시 녹음 종료
- **로컬 LLM 응답**: Ollama로 구동되는 `qwen2.5:3b`가 일반 대화에 응답
- **한국어 전용 응답**: 시스템 프롬프트 + 낮은 temperature로 중국어/일본어 혼입과 모델 자기소개("Qwen", "Alibaba Cloud" 등)를 차단. 그래도 새는 경우를 대비한 한자/가나 문자 탐지 안전망 적용
- **음성 합성(TTS)**: Microsoft Edge TTS — 텍스트에 한글 포함 여부를 자동 감지해 한국어(`ko-KR-InJoonNeural`)/영어(`en-GB-RyanNeural`) 음성을 자동 전환. 발화 속도 `+20%`로 응답 지연 단축. PowerShell 의존 없이 WSL 내부에서 `pygame`으로 직접 재생(WSLg PulseAudio 브리지 경유), 실패 시 `pyttsx3` 폴백
- **실시간 시간 조회**: "지금 몇 시야", "시간 알려줘" 등 → `datetime` 기반으로 LLM 호출 없이 즉시 답변
- **실시간 날짜 조회**: "오늘 날짜는", "오늘 무슨 요일이야" 등 → 마찬가지로 LLM 없이 즉시 답변
- **실시간 날씨 조회**: [Open-Meteo](https://open-meteo.com)(API 키 불필요)로 도시명을 추출해 현재 날씨/기온 조회. 도시명이 없으면 기본 도시(`서울`) 사용
- **실시간 웹 검색**: [Tavily](https://tavily.com) API로 최신 정보를 검색하고, Ollama로 결과를 한국어 1~2문장의 짧은 TTS용 답변으로 요약·번역
- **검색 오류 안내**: API 키 누락 / 한도 초과(Quota exceeded) / 네트워크 오류 / 기타 예외를 구분해 콘솔 로그(`[Search] ...`)와 사용자 친화적 음성 안내를 각각 다르게 제공
- **로컬 자동화**: Chrome / VS Code / 계산기 / 메모장 / 파일 탐색기 / 작업 관리자 / 설정 / Windows Terminal / Discord / 카카오톡 실행. 명령어 별칭 지원, 프로그램이 설치돼 있지 않으면 "~을 찾을 수 없습니다"로 자연스럽게 응답
- **처리 단계별 타이밍 로그**: 매 응답마다 `Recording`/`Whisper`/`Ollama`/`TTS`/`Total` 소요 시간을 콘솔에 출력해 성능 분석 가능

## 사용 예시

**일반 대화**
```
자비스 안녕
→ Jarvis: 안녕하세요! 무엇을 도와드릴까요?
```

**웨이크워드 오인식 보정 (fuzzy matching)**
```
사비스 안녕
→ Jarvis: (정상 인식, "안녕"으로 즉시 응답)

자빗스 오늘 몇 시야
→ Jarvis: (정상 인식, 시간으로 즉시 응답)
```

**실시간 시간/날짜**
```
자비스 지금 몇 시야
→ Jarvis: 현재 시간은 오후 11시 42분입니다.

자비스 오늘 날짜는
→ Jarvis: 오늘은 2026년 6월 24일 수요일입니다.

자비스 오늘 무슨 요일이야
→ Jarvis: 오늘은 2026년 6월 24일 수요일입니다.
```

**실시간 날씨**
```
자비스 부산 날씨 알려줘
→ Jarvis: 부산의 현재 날씨는 구름 조금, 기온은 21도입니다.
```

**실시간 웹 검색**
```
자비스 GPT-6 검색해줘
→ Jarvis: GPT-6은 2026년에 출시될 것으로 예상되지만, 정확한 날짜는 확인되지 않았습니다.
```

검색 한도를 다 썼거나 네트워크가 끊긴 경우엔 원인에 맞는 안내로 응답합니다.
```
(검색 한도 초과 시)
→ Jarvis: 이번 달 검색 한도를 모두 사용했습니다. 다음 달에 다시 이용할 수 있습니다.

(네트워크 오류 시)
→ Jarvis: 검색 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.
```

**로컬 자동화**
```
자비스 크롬 열어
→ Jarvis: 크롬을 실행합니다.

자비스 VS Code 열어
→ Jarvis: VS Code를 실행합니다.

자비스 디스코드 열어   (미설치 시)
→ Jarvis: 디스코드를 찾을 수 없습니다.
```

**기존 2단계 방식 (웨이크워드만 먼저 호출)**
```
자비스
→ Jarvis: 옛썰, 말씀하세요.
오늘 날씨 어때
→ Jarvis: 서울의 현재 날씨는 대체로 맑음, 기온은 20도입니다.
```

명령 처리가 끝나면 자동으로 대기(`IDLE`) 상태로 돌아갑니다.

### 지원 명령어 전체 목록

| 분류 | 예시 발화 | 동작 |
|---|---|---|
| 시간 | 지금 몇 시야 / 오늘 몇 시야 / 시간 알려줘 / 현재 시간 알려줘 | LLM 없이 즉시 응답 |
| 날짜 | 오늘 날짜는 / 오늘 며칠이야 / 오늘 무슨 요일이야 / 현재 날짜 알려줘 | LLM 없이 즉시 응답 |
| 날씨 | (도시명) 날씨 알려줘 / 오늘 날씨 어때 | Open-Meteo 실시간 조회 |
| 검색 | (검색어) 검색해줘 / 찾아줘 / 알려줘 | Tavily 실시간 검색 + 한국어 요약 |
| 자동화 | 크롬 열어 / VS Code 열어(=비주얼 스튜디오 코드 열어=코드 열어) / 계산기 열어 / 메모장 열어 / 탐색기 열어 / 작업 관리자 열어 / 설정 열어 / 터미널 열어 / 디스코드 열어 / 카카오톡 열어 | PowerShell `Start-Process` 실행 |
| 그 외 모든 발화 | (자유 대화) | Ollama(`qwen2.5:3b`)가 한국어로 응답 |

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 음성 캡처 | `parec` (PulseAudio, WSLg 오디오 브리지), RMS 기반 무음 감지(VAD) |
| STT | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CPU, int8) |
| LLM | [Ollama](https://ollama.com/) + `qwen2.5:3b` (HTTP API, `localhost:11434`) |
| TTS | [edge-tts](https://github.com/rany2/edge-tts) (Microsoft Edge Neural TTS) + `pygame.mixer` 재생, 실패 시 `pyttsx3` 폴백 |
| 실시간 날씨 | [Open-Meteo](https://open-meteo.com) (지오코딩 + 예보, API 키 불필요) |
| 실시간 검색 | [Tavily](https://tavily.com) Search API |
| 자동화 | Python `subprocess` + PowerShell `Start-Process` |
| 설정 | `python-dotenv` (`.env`) |
| 언어/런타임 | Python 3.12, WSL2 (Ubuntu) on Windows 11 |

## 프로젝트 구조

```
Jarvis-AI/
├── voice_recognition/
│   ├── recorder.py      # parec 마이크 녹음 + 무음 감지(VAD)로 자동 종료
│   ├── listener.py      # 녹음 + faster-whisper 전사, 단계별 소요 시간 기록
│   └── wake_word.py     # 웨이크워드("자비스") fuzzy 감지 + 명령 추출
├── llm/
│   └── ollama_client.py # Ollama HTTP API 클라이언트 (한국어 전용 시스템 프롬프트)
├── tts/
│   └── speaker.py       # Edge TTS 합성 + pygame 재생, pyttsx3 폴백
├── realtime/
│   ├── weather.py       # Open-Meteo 실시간 날씨 조회
│   └── search.py        # Tavily 실시간 웹 검색 + 한국어 요약
├── automation/
│   └── commands.py      # 명령어 매칭 + 로컬 프로그램 실행 + 시간/날짜 조회
├── config/
│   └── settings.py      # .env 기반 설정
├── assistant.py          # 상태 머신 (IDLE/LISTENING) + 의도 분기(날씨→명령→검색→LLM)
├── main.py               # 실행 진입점 (백그라운드 스레드로 메인 루프 실행)
├── requirements.txt
└── .env                  # (직접 생성, git에는 포함 안 됨)
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

루트에 `.env` 파일을 생성합니다. 전부 선택사항이며, 적지 않으면 아래 기본값이 적용됩니다.

```env
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_KEEP_ALIVE=30m

# 음성 인식
VOICE_LANGUAGE=ko
RECORD_SECONDS=8

# TTS (Edge TTS)
TTS_VOICE_KO=ko-KR-InJoonNeural
TTS_VOICE_EN=en-GB-RyanNeural
TTS_RATE=+20%
TTS_PITCH=-5Hz

# 실시간 정보
WEATHER_DEFAULT_CITY=서울
TAVILY_API_KEY=          # https://tavily.com 에서 무료 발급 (없으면 검색 기능만 비활성화)
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

## 향후 계획

- [ ] 대화 메모리 기능 (멀티턴 컨텍스트 유지)
- [ ] 앱 종료 기능 ("크롬 종료해" 등)
- [ ] 볼륨 제어 ("볼륨 올려줘" 등)
- [ ] XTTS/OpenVoice 기반 보이스 클로닝으로 더 "아이언맨 Jarvis"에 가까운 음성 구현
