"""음성에 깔린 잡음을 스펙트럼 게이팅으로 줄입니다.

main.py 가 자동으로 사용하며, 직접 실행하면 output/ 의 wav 를 처리해 output/clean/ 에 저장합니다.
"""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import ndimage, signal

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CLEAN_DIR = OUTPUT_DIR / "clean"

# ===== 잡음 제거 세기 =====
STRENGTH = 3.0  # 잰 잡음의 몇 배까지 지울지. 클수록 깨끗하지만 말소리가 뭉개질 수 있다
MAX_REDUCTION_DB = 24.0  # 최대로 줄이는 양(dB). 클수록 조용하지만 말끝·자음이 깎일 수 있다
HIGHPASS_HZ = 70.0  # 이보다 낮은 소리는 잘라 낸다
# ========================

# 분석 설정 (보통은 바꿀 필요 없음)
FRAME_SEC = 0.04  # 주파수를 분석하는 단위(초)
QUIET_BELOW_PEAK_DB = 40.0  # 가장 큰 구간보다 이만큼 작으면 말이 없는 구간으로 본다
DIGITAL_SILENCE_DB = -100.0  # 이보다 작은 완전한 무음은 잡음 측정에서 뺀다
MIN_QUIET_SEC = 0.05  # 잡음을 재는 데 필요한 최소 조용한 구간 길이(초)
GUARD_SEC = 0.03  # 약한 자음·말끝을 보호하려고 말소리 앞뒤로 남기는 길이(초)
GATE_FADE_SEC = 0.03  # 말이 없는 구간의 소리 크기가 바뀌는 데 걸리는 시간(초)


def find_pauses(power: np.ndarray, frame_sec: float) -> np.ndarray:
    """프레임마다 말이 없는 구간인지 표시합니다.

    Args:
        power: 주파수별·프레임별 파워 스펙트로그램.
        frame_sec: 프레임 간격(초).

    Returns:
        말이 없는 프레임이 True 인 배열.
    """
    levels = 10 * np.log10(power.sum(axis=0) + 1e-20)
    speech = levels >= levels.max() - QUIET_BELOW_PEAK_DB
    guard = max(1, round(GUARD_SEC / frame_sec))
    return ~ndimage.binary_dilation(speech, iterations=guard)


def reduce_noise(wav: np.ndarray, sr: int) -> np.ndarray:
    """음성에서 저음 웅웅거림, 일정한 잡음, 말 사이의 작은 소리를 줄입니다.

    Args:
        wav: 음성 샘플.
        sr: 샘플레이트(Hz).

    Returns:
        입력과 길이·자료형이 같은, 잡음을 줄인 음성.
    """
    sos = signal.butter(4, HIGHPASS_HZ, btype="highpass", fs=sr, output="sos")
    filtered = signal.sosfiltfilt(sos, wav)

    size = int(sr * FRAME_SEC)
    hop = size // 4
    frame_sec = hop / sr
    _, _, spec = signal.stft(filtered, sr, nperseg=size, noverlap=size - hop)
    power = np.abs(spec) ** 2

    pauses = find_pauses(power, frame_sec)
    floor = 10 ** (-MAX_REDUCTION_DB / 20)

    # 일정한 잡음: 주파수별로 잡음보다 충분히 크지 않은 성분을 줄인다
    measurable = pauses & (10 * np.log10(power.mean(axis=0) + 1e-20) > DIGITAL_SILENCE_DB)
    if measurable.sum() * frame_sec >= MIN_QUIET_SEC:
        # 중앙값을 쓰면 숨소리가 섞여도 잡음 측정값이 끌려가지 않는다
        noise = np.median(power[:, measurable], axis=1, keepdims=True)
        # 주변과 평균 내서 판단해야 뽀글거리는 잔여 소리(뮤지컬 노이즈)가 생기지 않는다
        smoothed = ndimage.uniform_filter(power, size=(3, 5))
        gain = np.sqrt(np.clip(1 - STRENGTH * noise / (smoothed + 1e-20), floor**2, 1))
        gain = ndimage.uniform_filter(gain, size=(3, 3))
    else:
        gain = np.ones_like(power)

    # 말 사이의 작은 소리: 말이 없는 구간 전체를 줄이고 경계는 부드럽게 잇는다
    fade = max(1, round(GATE_FADE_SEC / frame_sec))
    pause_gain = ndimage.uniform_filter1d(np.where(pauses, floor, 1.0), size=fade)
    gain = np.minimum(gain, pause_gain)

    _, cleaned = signal.istft(spec * gain, sr, nperseg=size, noverlap=size - hop)
    return cleaned[: len(wav)].astype(wav.dtype)


def main() -> None:
    """명령줄에서 지정한 wav 의 잡음을 줄여 output/clean/ 에 저장합니다."""
    parser = argparse.ArgumentParser(description="output/ 의 wav 에서 잡음을 줄여 output/clean/ 에 저장합니다.")
    parser.add_argument("names", nargs="*", help="처리할 파일 이름 (생략하면 output/ 의 모든 .wav)")
    args = parser.parse_args()

    if args.names:
        paths = [OUTPUT_DIR / (name if name.endswith(".wav") else f"{name}.wav") for name in args.names]
        for path in paths:
            if not path.is_file():
                raise SystemExit(f"음성 파일을 찾을 수 없습니다: {path}")
    else:
        paths = sorted(OUTPUT_DIR.glob("*.wav"))
    if not paths:
        raise SystemExit(f"처리할 음성이 없습니다. {OUTPUT_DIR} 에 .wav 파일이 있는지 확인해 주세요.")

    CLEAN_DIR.mkdir(exist_ok=True)
    for path in paths:
        wav, sr = sf.read(path, dtype="float32")
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        sf.write(CLEAN_DIR / path.name, reduce_noise(wav, sr), sr)
        print(f"완료: {CLEAN_DIR / path.name}")


if __name__ == "__main__":
    main()
