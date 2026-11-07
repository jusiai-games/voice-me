# voice-me

**내 목소리로 글을 읽어 주는 프로그램입니다.**

내 목소리를 5~15초 녹음한 파일과 읽을 글(대본)을 넣으면, 내 목소리로 대본을 읽은 음성 파일(wav)을 만들어 줍니다. 인공지능 모델 [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) 0.6B 를 내 컴퓨터에서 직접 실행합니다. 인터넷은 설치할 때와 첫 실행 때 모델을 내려받을 때만 사용하고, 그 뒤로는 인터넷 없이 실행됩니다.

> **NVIDIA GPU 전용입니다.** NVIDIA 그래픽카드가 있는 PC 에서만 실행할 수 있습니다. Mac 과 그래픽카드가 없는 PC, AMD·Intel 그래픽카드만 있는 PC 는 지원하지 않습니다.

> **꼭 지켜 주세요:** 본인의 목소리 또는 **당사자의 동의를 받은** 목소리만 사용하세요. 다른 사람을 사칭하거나 속이는 데 사용해서는 안 됩니다.

## 시작하기 전에

| 항목 | 내용 |
| --- | --- |
| 그래픽카드 | **NVIDIA GPU 필수** (CUDA 12.6 을 지원하는 최신 드라이버 설치) |
| 운영체제 | Windows, Linux |
| Python | **3.12** 버전 ([내려받기](https://www.python.org/downloads/)) |
| 저장 공간 | 10GB 이상 (설치 파일과 모델이 큽니다) |

- RTX 2070 이 달린 Windows PC 에서 확인했습니다.
- 대본은 **한국어**로 읽도록 설정되어 있습니다.

## 1단계: 프로그램 내려받기

이 페이지 위쪽의 초록색 **Code** 버튼 → **Download ZIP** 을 누르고, 받은 파일의 압축을 풀어 주세요.

## 2단계: 설치하기 (처음 한 번만)

설치는 시간이 꽤 걸립니다. 인터넷 속도에 따라 수십 분이 걸릴 수 있습니다.

### Windows

`bin` 폴더의 **`setup.bat`** 을 더블클릭합니다.

### Linux

터미널을 열고, `voice-me` 폴더로 이동한 뒤 아래 명령을 실행합니다.

```bash
bash bin/setup.sh
```

## 3단계: 내 파일 준비하기

아래 세 가지 파일을 넣어 주세요.

```
voice-me/
├── reference/
│   ├── ref.wav       ① 내 목소리 녹음
│   └── ref.txt       ② 녹음에서 읽은 문장
└── scripts/
    └── intro.txt     ③ 읽어 줄 대본 (이름은 자유롭게, 여러 개 가능)
```

### ① 내 목소리 녹음: `reference/ref.wav`

- 조용한 곳에서 평소 말투로 **5~15초** 녹음합니다.
- 파일 이름을 `ref.wav` 로 저장합니다. **wav 형식이어야 합니다.**
- 녹음 앱이 m4a 나 mp3 로 저장한다면, 무료 프로그램 [Audacity](https://www.audacityteam.org/) 로 파일을 연 뒤 wav 로 내보내면 됩니다.

### ② 녹음에서 읽은 문장: `reference/ref.txt`

메모장 같은 프로그램으로 녹음에서 말한 문장을 **글자 그대로** 적어 저장합니다. 녹음 내용과 다르면 결과 음질이 떨어집니다.

### ③ 대본: `scripts/` 폴더

읽어 줄 글을 `.txt` 파일로 저장합니다. 메모장에서 저장하면 됩니다. **파일 이름이 결과 파일 이름**이 됩니다.

```
scripts/intro.txt       →  output/intro.wav
scripts/episode-01.txt  →  output/episode-01.wav
```

## 4단계: 음성 만들기

### Windows

`bin` 폴더의 **`run.bat`** 을 더블클릭합니다.

### Linux

```bash
bash bin/run.sh
```

`scripts/` 안의 대본을 모두 읽어서 **`output` 폴더**에 wav 파일로 저장합니다.

- 첫 실행 때는 모델(약 2.4GB)을 내려받느라 시간이 더 걸립니다. 처음 한 번만 받습니다.
- 같은 이름의 파일이 이미 있으면 **새 파일로 덮어씁니다.**

### 특정 대본만 만들기

대본 이름을 뒤에 적으면 됩니다. (`.txt` 는 생략 가능)

```bash
bin\run.bat intro episode-01          # Windows
bash bin/run.sh intro episode-01      # Linux
```

> Windows 에서는 `voice-me` 폴더를 열고, 탐색기 주소창에 `cmd` 를 입력하고 Enter 를 누르면 명령 창이 열립니다.

## 이미 만든 음성 다듬기

음성을 만들 때 잡음 제거와 긴 쉼 줄이기가 자동으로 적용됩니다. 이미 있는 파일에 다시 적용하고 싶을 때만 아래 스크립트를 사용하세요. 원본은 그대로 남습니다.

| 하고 싶은 일 | Windows | Linux | 결과 위치 |
| --- | --- | --- | --- |
| 잡음 줄이기 | `bin\denoise.bat` | `bash bin/denoise.sh` | `output/clean/` |
| 긴 쉼 줄이기 | `bin\pauses.bat` | `bash bin/pauses.sh` | `output/tight/` |

`run` 과 마찬가지로 이름을 적지 않으면 `output/` 의 모든 wav 를, 이름을 적으면 해당 파일만 처리합니다.

## 결과가 마음에 들지 않을 때

`src` 폴더의 파이썬 파일 맨 위에 있는 설정값을 메모장으로 고칠 수 있습니다.

| 증상 | 파일 | 바꿀 값 |
| --- | --- | --- |
| 잡음이 남아 있음 | `src/denoise.py` | `STRENGTH`, `MAX_REDUCTION_DB` 를 키우기 |
| 말끝이나 자음이 깎임 | `src/denoise.py` | `STRENGTH`, `MAX_REDUCTION_DB` 를 줄이기 |
| 말이 너무 붙어서 들림 | `src/pauses.py` | `MAX_PAUSE_SEC` 를 키우기 |
| 말이 늘어짐 | `src/pauses.py` | `MAX_PAUSE_SEC` 를 줄이기 |
| 말끝의 여운 길이 조절 | `src/main.py` | `TAIL_SILENCE_SEC` |
| 잡음 제거를 끄기 | `src/main.py` | `DENOISE` 를 `False` 로 |
| 쉼 줄이기를 끄기 | `src/main.py` | `SHORTEN_PAUSES` 를 `False` 로 |

목소리가 닮지 않았다면 프로그램 설정보다 **녹음을 다시 하는 것**이 가장 효과적입니다. 조용한 곳에서 또박또박 녹음하고, `ref.txt` 가 녹음 내용과 똑같은지 확인해 주세요.

## 문제 해결

| 나타나는 메시지 / 증상 | 해결 방법 |
| --- | --- |
| `NVIDIA GPU 를 찾지 못했습니다` / `인식하지 못했습니다` | NVIDIA 그래픽카드가 있는 PC 인지 확인하고, [NVIDIA 드라이버](https://www.nvidia.com/Download/index.aspx)를 최신 버전으로 설치하세요. 그래픽카드가 없으면 실행할 수 없습니다. |
| `Python 3.12 가 필요합니다` | Python 3.12 를 설치하고 setup 을 다시 실행하세요. |
| `환경이 준비되지 않았습니다` | 2단계의 setup 을 먼저 실행하세요. |
| `내 목소리 녹음 파일이 없습니다` | `reference` 폴더에 `ref.wav` 가 있는지 확인하세요. |
| `녹음에서 읽은 문장을 이 파일에 적어 주세요` | `reference/ref.txt` 를 만들고 문장을 적어 주세요. |
| `읽을 대본이 없습니다` | `scripts` 폴더에 내용이 있는 `.txt` 파일을 넣어 주세요. |
| 파일을 넣었는데 찾지 못함 | 파일 이름이 `ref.txt.txt` 처럼 되어 있지 않은지 확인하세요. 탐색기의 **보기 → 파일 확장명**을 켜면 보입니다. |
| `가상환경을 만들지 못했습니다` (Ubuntu) | `sudo apt install python3.12-venv` 를 실행한 뒤 setup 을 다시 실행하세요. |
| `Windows의 PC 보호` 창이 뜸 | **추가 정보 → 실행**을 누르세요. |
| `flash-attn is not installed`, `SoX could not be found!` | 안내 메시지입니다. 무시해도 됩니다. |
| 그래픽 메모리 부족 오류 (`out of memory`) | 다른 프로그램을 닫거나, 대본을 여러 파일로 나눠 주세요. |

## 개인정보 안내

녹음(`reference/`), 대본(`scripts/`), 생성된 음성(`output/`)은 `.gitignore` 로 제외되어 있어 git 저장소에 올라가지 않습니다.

## 개발자용

```
voice-me/
├── bin/                  # 환경 준비·실행 스크립트 (Windows: .bat, Linux: .sh)
├── src/
│   ├── main.py           # 음성 생성
│   ├── denoise.py        # 잡음 제거
│   └── pauses.py         # 긴 쉼 줄이기
├── reference/            # 레퍼런스 음성과 문장 (git 제외)
├── scripts/              # 대본 (git 제외)
├── output/               # 생성된 음성 (git 제외)
├── requirements.txt      # 실행에 필요한 패키지
├── requirements-dev.txt  # 개발용 패키지 (ruff)
└── pyproject.toml        # ruff 설정
```

- `requirements.txt` 는 CUDA 12.6 용 PyTorch 를 설치합니다. 다른 CUDA 버전을 쓰려면 이 파일을 수정하세요.
- 모델은 `src/main.py` 의 `MODEL_REVISION` 에 적힌 커밋으로 고정되어 있습니다. 모델을 업데이트하려면 이 값을 바꾸세요.

린트와 포맷팅: 가상환경을 활성화하지 않아도 됩니다. Linux 에서는 `.venv\Scripts\python.exe` 대신 `.venv/bin/python` 을 사용하세요.

```bash
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format .
```
