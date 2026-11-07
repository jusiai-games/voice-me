"""Qwen3-TTS 0.6B 로 scripts/ 의 대본을 내 목소리로 읽어 output/ 에 wav 로 저장합니다.

처리 순서: 대본 읽기 → 모델 불러오기 → 목소리 정보 만들기 → 대본마다 음성 생성·잡음 제거·쉼 줄이기·말끝 다듬기
"""

import argparse
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import snapshot_download
from huggingface_hub.errors import LocalEntryNotFoundError
from qwen_tts import Qwen3TTSModel

from denoise import reduce_noise
from pauses import shorten_pauses

BASE_DIR = Path(__file__).resolve().parent.parent

# ===== 설정 =====
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
MODEL_REVISION = "5d83992436eae1d760afd27aff78a71d676296fc"  # 저장소가 바뀌어도 이 버전의 모델만 받는다
MODEL_READY_FILE = ".voice-me-ready"  # 내려받기가 끝난 모델 폴더에 남기는 표시
REF_AUDIO = BASE_DIR / "reference" / "ref.wav"  # 내 목소리 녹음 (5~15초, wav)
REF_TEXT_FILE = BASE_DIR / "reference" / "ref.txt"  # 녹음에서 읽은 문장
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output"
DTYPE = torch.float32  # RTX 20 시리즈는 float16 에서 계산이 넘쳐 오류가 난다
DENOISE = True  # 잡음 제거 여부 (세기는 denoise.py 에서 설정)
SHORTEN_PAUSES = True  # 긴 쉼 줄이기 여부 (길이는 pauses.py 에서 설정)
FADE_OUT_SEC = 0.15  # 말끝을 서서히 줄이는 길이(초)
FADE_MID_GAIN = 0.8  # 줄이는 구간 한가운데의 소리 크기. 클수록 끝까지 크게 유지된다
TAIL_SILENCE_SEC = 0.5  # 말이 끝난 뒤 붙이는 무음 길이(초)
# ================

# 말끝 찾기 설정 (보통은 바꿀 필요 없음)
LEVEL_WINDOW_SEC = 0.02  # 소리 크기를 재는 단위(초)
SILENCE_RATIO = 0.02  # 가장 큰 소리의 이 비율보다 작으면 무음으로 본다
SPEECH_END_MARGIN_SEC = 0.03  # 숨소리·잔향을 보호하려고 말끝 뒤에 남기는 길이(초)


def find_speech_end(wav: np.ndarray, sr: int) -> int:
    """말소리가 실제로 끝나는 위치를 찾습니다.

    Args:
        wav: 음성 샘플.
        sr: 샘플레이트(Hz).

    Returns:
        말끝의 샘플 번호. 소리를 찾지 못하면 음성 전체 길이.
    """
    win = int(sr * LEVEL_WINDOW_SEC)
    n = len(wav) // win
    if n == 0:
        return len(wav)
    levels = np.sqrt((wav[: n * win].reshape(n, win) ** 2).mean(axis=1))
    threshold = max(levels.max() * SILENCE_RATIO, 1e-3)
    loud = np.nonzero(levels > threshold)[0]
    if len(loud) == 0:
        return len(wav)
    end = (loud[-1] + 1) * win + int(sr * SPEECH_END_MARGIN_SEC)
    return min(len(wav), end)


def fade_out_curve(length: int) -> np.ndarray:
    """1 에서 0 으로 줄어드는 소리 크기 곡선(1 - t^p)을 만듭니다.

    Args:
        length: 곡선의 샘플 수.

    Returns:
        한가운데 값이 FADE_MID_GAIN 인 곡선.
    """
    p = np.log(1 - FADE_MID_GAIN) / np.log(0.5)
    return 1 - np.linspace(0, 1, length) ** p


def finish_tail(wav: np.ndarray, sr: int) -> np.ndarray:
    """뒤쪽 무음을 자르고, 말끝을 서서히 줄인 뒤, 여운 무음을 붙입니다.

    Args:
        wav: 음성 샘플.
        sr: 샘플레이트(Hz).

    Returns:
        말끝을 다듬은 음성.
    """
    wav = wav[: find_speech_end(wav, sr)].copy()
    fade = min(len(wav), int(sr * FADE_OUT_SEC))
    if fade > 0:
        wav[-fade:] *= fade_out_curve(fade).astype(wav.dtype)
    silence = np.zeros(int(sr * TAIL_SILENCE_SEC), dtype=wav.dtype)
    return np.concatenate([wav, silence])


def load_scripts(names: list[str]) -> list[tuple[Path, str]]:
    """변환할 대본들을 읽습니다. 빈 파일은 건너뜁니다.

    Args:
        names: 대본 이름 목록(.txt 생략 가능). 비어 있으면 scripts/ 의 모든 .txt.

    Returns:
        (파일 경로, 대본 내용) 목록.
    """
    if names:
        paths = []
        for name in names:
            path = SCRIPTS_DIR / (name if name.endswith(".txt") else f"{name}.txt")
            if not path.is_file():
                raise SystemExit(f"대본 파일을 찾을 수 없습니다: {path}")
            paths.append(path)
    else:
        paths = sorted(SCRIPTS_DIR.glob("*.txt"))

    scripts = []
    for path in paths:
        # utf-8-sig: 메모장에서 저장한 BOM 포함 파일도 읽는다
        text = path.read_text(encoding="utf-8-sig").strip()
        if not text:
            print(f"건너뜀 (빈 파일): {path.name}")
            continue
        scripts.append((path, text))
    if not scripts:
        raise SystemExit(f"읽을 대본이 없습니다. {SCRIPTS_DIR} 에 .txt 파일을 넣어 주세요.")
    return scripts


def load_reference() -> tuple[np.ndarray, int]:
    """내 목소리 녹음을 모노로 읽고, 최대 음량을 0.95 로 맞춥니다.

    Returns:
        (음성 샘플, 샘플레이트).
    """
    if not REF_AUDIO.is_file():
        raise SystemExit(f"내 목소리 녹음 파일이 없습니다: {REF_AUDIO}")
    wav, sr = sf.read(REF_AUDIO, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    peak = float(abs(wav).max())
    if peak > 0:
        wav = wav / peak * 0.95
    print(f"참고 음성: {len(wav) / sr:.1f}초, 원래 최대 음량 {peak:.2f} → 0.95로 맞춤")
    return wav, sr


def load_reference_text() -> str:
    """녹음에서 읽은 문장을 읽습니다.

    Returns:
        reference/ref.txt 의 내용.
    """
    text = REF_TEXT_FILE.read_text(encoding="utf-8-sig").strip() if REF_TEXT_FILE.is_file() else ""
    if not text:
        raise SystemExit(f"녹음에서 읽은 문장을 이 파일에 적어 주세요: {REF_TEXT_FILE}")
    return text


def prepare_model() -> str:
    """고정된 버전의 모델을 준비합니다. 내려받은 적이 있으면 인터넷에 접속하지 않습니다.

    Returns:
        내려받은 모델 폴더 경로.
    """
    try:
        path = Path(snapshot_download(MODEL_ID, revision=MODEL_REVISION, local_files_only=True))
        if (path / MODEL_READY_FILE).is_file():
            return str(path)
    except LocalEntryNotFoundError:
        pass

    print("모델 내려받는 중... (약 2.4GB, 처음 한 번만 받습니다)")
    path = Path(snapshot_download(MODEL_ID, revision=MODEL_REVISION))
    (path / MODEL_READY_FILE).touch()
    return str(path)


def main() -> None:
    """명령줄에서 지정한 대본을 음성으로 변환해 저장합니다."""
    parser = argparse.ArgumentParser(
        description="scripts/ 의 txt 대본을 내 목소리로 읽어 output/ 에 wav 로 저장합니다."
    )
    parser.add_argument("names", nargs="*", help="변환할 대본 이름 (생략하면 scripts/ 의 모든 .txt)")
    args = parser.parse_args()

    # 오래 걸리는 모델 로딩 전에 입력 파일부터 확인한다
    scripts = load_scripts(args.names)
    print(f"대본 {len(scripts)}개: {', '.join(path.name for path, _ in scripts)}")
    reference = load_reference()
    reference_text = load_reference_text()
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not torch.cuda.is_available():
        raise SystemExit(
            "NVIDIA GPU 를 인식하지 못했습니다. 이 프로그램은 NVIDIA GPU 가 있는 PC 에서만 실행할 수 있습니다."
        )
    print("사용 GPU:", torch.cuda.get_device_name(0))

    model_path = prepare_model()
    print("모델 불러오는 중...")
    model = Qwen3TTSModel.from_pretrained(
        model_path,
        device_map="cuda:0",
        dtype=DTYPE,
        attn_implementation="sdpa",  # RTX 20 시리즈는 FlashAttention 을 지원하지 않는다
    )

    # 목소리 정보를 한 번만 만들어 모든 대본에 재사용한다
    voice = model.create_voice_clone_prompt(ref_audio=reference, ref_text=reference_text)

    for i, (script_path, text) in enumerate(scripts, start=1):
        output_path = OUTPUT_DIR / f"{script_path.stem}.wav"
        print(f"[{i}/{len(scripts)}] {script_path.name} ({len(text)}자) 생성 중...")
        start = time.time()
        wavs, sr = model.generate_voice_clone(text=text, language="Korean", voice_clone_prompt=voice)
        wav = reduce_noise(wavs[0], sr) if DENOISE else wavs[0]
        wav = shorten_pauses(wav, sr) if SHORTEN_PAUSES else wav
        wav = finish_tail(wav, sr)
        sf.write(output_path, wav, sr)
        print(f"  완료: {output_path} ({len(wav) / sr:.1f}초 분량, 생성에 {time.time() - start:.1f}초 걸림)")


if __name__ == "__main__":
    main()
