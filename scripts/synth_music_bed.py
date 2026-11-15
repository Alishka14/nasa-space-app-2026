#!/usr/bin/env python3
"""Synthesise a calm instrumental background bed for the EARTH SENSES films. No samples, no credits, no licences.

    python scripts/synth_music_bed.py docs/video/music/earth_senses_bed.wav [seconds]

Additive synthesis only (same idea as Pavlodar Pulse's synthesised splash sound): a slow four-chord pad
(Am9 – Fmaj7 – Cadd9 – G6sus, 8 s each) of soft detuned partials, a low A drone, sparse bell-like notes from the
current chord and a synthetic hall reverb (decaying noise impulse response). Seeded, so the file is reproducible.
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
SEED = 2026
CHORD_S = 8.0
# MIDI notes, mid register; the first is the chord root
CHORDS = [
    [57, 60, 64, 67, 71],   # Am9 (A C E G B)
    [53, 57, 60, 64, 69],   # Fmaj7 (F A C E A)
    [48, 55, 60, 62, 64],   # Cadd9 (C G C D E)
    [55, 59, 62, 64, 69],   # G6sus-ish (G B D E A)
]


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def soft_tone(f: float, t: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Mellow tone: first 6 harmonics at 1/n^2, three voices detuned by a few cents."""
    out = np.zeros_like(t)
    for cents in (-4.0, 0.0, 4.5):
        ff = f * 2 ** (cents / 1200)
        for n in range(1, 7):
            out += np.sin(2 * np.pi * ff * n * t + rng.uniform(0, 2 * np.pi)) / n ** 2
    return out / 3


def envelope(n: int, attack: float, release: float) -> np.ndarray:
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    e[-r:] = np.cos(np.linspace(0, np.pi / 2, r)) ** 2
    return e


def main(dst: Path, seconds: float) -> None:
    rng = np.random.default_rng(SEED)
    n = int(seconds * SR)
    L, R = np.zeros(n), np.zeros(n)

    # pad: each chord lasts CHORD_S plus a 3 s overlap with the next one
    k = 0
    start = 0.0
    while start < seconds:
        chord = CHORDS[k % len(CHORDS)]
        dur = min(CHORD_S + 3.0, seconds - start)
        i0, m = int(start * SR), int(dur * SR)
        t = np.arange(m) / SR
        env = envelope(m, 2.5, min(3.0, dur / 2))
        for j, note in enumerate(chord):
            lfo = 1 + 0.18 * np.sin(2 * np.pi * (0.05 + 0.013 * j) * t + rng.uniform(0, 6.3))
            tone = soft_tone(hz(note), t, rng) * env * lfo * (0.9 if j == 0 else 0.6)
            pan = 0.5 + 0.35 * (-1) ** j * (0.4 + 0.15 * j)
            L[i0:i0 + m] += tone * np.sqrt(1 - pan)
            R[i0:i0 + m] += tone * np.sqrt(pan)
        start += CHORD_S
        k += 1

    # low drone on A, slowly breathing
    t = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 55 * t) * 0.6 + np.sin(2 * np.pi * 110 * t + 1.0) * 0.25)
    drone *= 0.55 + 0.15 * np.sin(2 * np.pi * 0.04 * t)
    L += drone * 0.3
    R += drone * 0.3

    # sparse bell-like notes from the current chord, one octave up
    tb = 1.5
    while tb < seconds - 3:
        chord = CHORDS[int(tb // CHORD_S) % len(CHORDS)]
        f = hz(rng.choice(chord[1:]) + 12)
        m = int(3.5 * SR)
        i0 = int(tb * SR)
        m = min(m, n - i0)
        tt = np.arange(m) / SR
        bell = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt) +
                0.08 * np.sin(2 * np.pi * 3.01 * f * tt)) * np.exp(-tt / 0.9)
        bell[: int(0.006 * SR)] *= np.linspace(0, 1, int(0.006 * SR))
        pan = rng.uniform(0.25, 0.75)
        L[i0:i0 + m] += bell * 0.6 * np.sqrt(1 - pan)
        R[i0:i0 + m] += bell * 0.6 * np.sqrt(pan)
        tb += rng.uniform(3.5, 6.0)

    # warm it up: low-pass the dry signal
    sos = butter(2, 3200, btype="low", fs=SR, output="sos")
    hp = butter(2, 45, btype="high", fs=SR, output="sos")   # no sub-rumble
    L, R = sosfilt(hp, sosfilt(sos, L)), sosfilt(hp, sosfilt(sos, R))

    # hall reverb: decaying, low-passed noise impulse response, decorrelated per channel, 25 ms pre-delay
    rt60 = 3.2
    ir_n = int(rt60 * SR)
    tir = np.arange(ir_n) / SR
    decay = np.exp(-6.9 * tir / rt60)
    sos_ir = butter(2, 4500, btype="low", fs=SR, output="sos")
    pre = np.zeros(int(0.025 * SR))
    irl = np.concatenate([pre, sosfilt(sos_ir, rng.standard_normal(ir_n)) * decay])
    irr = np.concatenate([pre, sosfilt(sos_ir, rng.standard_normal(ir_n)) * decay])
    irl /= np.sqrt(np.sum(irl ** 2))
    irr /= np.sqrt(np.sum(irr ** 2))
    wl, wr = fftconvolve(L, irl)[:n], fftconvolve(R, irr)[:n]
    L, R = 0.7 * L + 0.55 * wl, 0.7 * R + 0.55 * wr

    # overall fades and peak level -3 dBFS
    fade = envelope(n, 2.0, 4.0)
    L, R = L * fade, R * fade
    peak = max(np.abs(L).max(), np.abs(R).max())
    g = 10 ** (-3 / 20) / peak
    pcm = (np.stack([L, R], axis=1) * g * 32767).astype("<i2")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"{dst}: {seconds:.1f} s, stereo {SR} Hz")


if __name__ == "__main__":
    main(Path(sys.argv[1]), float(sys.argv[2]) if len(sys.argv) > 2 else 72.0)
