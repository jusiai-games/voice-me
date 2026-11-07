"""말 사이의 긴 쉼을 줄입니다. 말소리는 건드리지 않아 음높이·음질이 그대로입니다.

main.py 가 자동으로 사용하며, 직접 실행하면 output/ 의 wav 를 처리해 output/tight/ 에 저장합니다.
"""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
TIGHT_DIR = OUTPUT_DIR / "tight"

# ===== 쉼 길이 =====
MAX_PAUSE_SEC = 0.3  # 쉼의 최대 길이(초). 작을수록 빠르게 들리지만 숨 돌릴 틈이 줄어든다
# ==================

# 분석 설정 (보통은 바꿀 필요 없음)
LEVEL_WINDOW_SEC = 0.02  # 소리 크기를 재는 단위(초)
QUIET_BELOW_PEAK_DB = 40.0  # 가장 큰 소리보다 이만큼 작으면 말이 없는 구간으로 본다
FADE_SEC = 0.01  # 자른 자리가 튀지 않도록 소리를 줄이고 키우는 길이(초)


def find_cuts(wav: np.ndarray, sr: int) -> list[tuple[int, int]]:
    """잘라 낼 구간을 찾습니다. 맨 앞과 맨 뒤의 무음은 건드리지 않습니다.

    Args:
        wav: 음성 샘플.
        sr: 샘플레이트(Hz).

    Returns:
        잘라 낼 구간의 (시작, 끝) 샘플 번호 목록.
    """
    win = int(sr * LEVEL_WINDOW_SEC)
    n = len(wav) // win
    if n == 0:
        return []
    levels = 10 * np.log10((wav[: n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-20)
    speech = np.nonzero(levels >= levels.max() - QUIET_BELOW_PEAK_DB)[0]

    # 말끝의 잔향과 다음 말의 시작을 지키려고 쉼의 양 끝을 남긴다
    keep = int(sr * MAX_PAUSE_SEC) // 2
    cuts = []
    for before, after in zip(speech[:-1], speech[1:], strict=True):
        start = (before + 1) * win + keep
        end = after * win - keep
        if end > start:
            cuts.append((int(start), int(end)))
    return cuts


def shorten_pauses(wav: np.ndarray, sr: int) -> np.ndarray:
    """긴 쉼의 가운데를 잘라 MAX_PAUSE_SEC 로 줄입니다.

    Args:
        wav: 음성 샘플.
        sr: 샘플레이트(Hz).

    Returns:
        쉼을 줄인 음성.
    """
    cuts = find_cuts(wav, sr)
    if not cuts:
        return wav

    wav = wav.copy()
    fade = int(sr * FADE_SEC)
    ramp = np.linspace(1, 0, fade, dtype=wav.dtype)
    pieces = []
    position = 0
    for start, end in cuts:
        wav[start - fade : start] *= ramp
        wav[end : end + fade] *= ramp[::-1]
        pieces.append(wav[position:start])
        position = end
    pieces.append(wav[position:])
    return np.concatenate(pieces)


def main() -> None:
    """명령줄에서 지정한 wav 의 긴 쉼을 줄여 output/tight/ 에 저장합니다."""
    parser = argparse.ArgumentParser(description="output/ 의 wav 에서 긴 쉼을 줄여 output/tight/ 에 저장합니다.")
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

    TIGHT_DIR.mkdir(exist_ok=True)
    for path in paths:
        wav, sr = sf.read(path, dtype="float32")
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        tight = shorten_pauses(wav, sr)
        sf.write(TIGHT_DIR / path.name, tight, sr)
        print(f"완료: {TIGHT_DIR / path.name} ({len(wav) / sr:.1f}초 → {len(tight) / sr:.1f}초)")


if __name__ == "__main__":
    main()
