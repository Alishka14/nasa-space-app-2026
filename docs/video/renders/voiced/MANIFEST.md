# Voiced films

Made by `scripts/build_voiced_films.py` from the silent renders in `docs/video/renders/` and one ElevenLabs speech clip per scene (texts: `docs/video/voiceover_lines.json`). The voice is synthetic and every file says so in the picture ("AI voice (ElevenLabs)") and in its metadata. Background music: synthesised by scripts/synth_music_bed.py (procedural, no samples).

| File | Status | Length | Silent original | Slowest scene | Size |
|---|---|---|---|---|---|
| `demo_en_voice.mp4` | DONE | 29.3 s | 29.3 s | ×1.00 | 10.2 MB |
| `hero_en_voice.mp4` | DONE | 60.9 s | 59.5 s | ×1.17 | 19.5 MB |
| `hero_ru_voice.mp4` | DONE | 65.1 s | 59.5 s | ×1.33 | 20.5 MB |
| `hero_kk_voice.mp4` | DONE | 65.0 s | 59.5 s | ×1.47 | 20.5 MB |
| `explainer_en_voice.mp4` | DONE | 53.4 s | 45.0 s | ×1.40 | 10.0 MB |
| `explainer_ru_voice.mp4` | DONE | 63.3 s | 45.0 s | ×1.83 | 11.2 MB |
| `explainer_kk_music.mp4` | no voice (lines e3, e5, e7 missing) — subtitles + music | 45.0 s | 45.0 s | ×1.00 | 8.7 MB |
| `teaser_en_voice.mp4` | DONE | 18.9 s | 16.5 s | ×1.48 | 7.2 MB |
| `teaser_ru_voice.mp4` | DONE | 23.2 s | 16.5 s | ×2.07 | 7.9 MB |
| `teaser_kk_music.mp4` | no voice (lines t2, t4 missing) — subtitles + music | 16.5 s | 16.5 s | ×1.00 | 6.7 MB |

Loudness: two-pass EBU R128 normalisation to −16 LUFS (music-only files −20 LUFS); true peak after AAC encoding ≤ −1.3 dBTP. Music bed (when used): ducked under speech, faded in/out per film.
Subtitles: `<film>_voice.srt` are the films' on-screen subtitles re-timed to the slowed scenes.
