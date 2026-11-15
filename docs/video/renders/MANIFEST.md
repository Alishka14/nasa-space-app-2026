# Recorded films

Screen recordings of the running app, made frame by frame with `scripts/record_intro.mjs` (in-app intro, 1280×720 layout rendered at 1920×1080, software WebGL) and `scripts/make_demo.sh` (the 30-second demo, from the Short intro and screenshots of the app). Not generated footage. Silent: the narration is in the picture as subtitles. SRT files for every film and language are in `../subtitles/` (upload the English file as captions when publishing a Russian or Kazakh film). Regenerate this list with `python scripts/package_videos.py`.

| File | Length | Picture | Size | Decodes cleanly | SHA-256 |
|---|---|---|---|---|---|
| [`demo_en.mp4`](demo_en.mp4) | 29.3 s | 1920×1080, 24 fps H264 | 10.1 MB | yes | `fc0764018d2c3b64…` |
| [`explainer_en.mp4`](explainer_en.mp4) | 45.0 s | 1920×1080, 24 fps H264 | 7.6 MB | yes | `ef3810dcfcb7abbd…` |
| [`explainer_kk.mp4`](explainer_kk.mp4) | 45.0 s | 1920×1080, 24 fps H264 | 7.8 MB | yes | `b58bf5f8d47fb280…` |
| [`explainer_ru.mp4`](explainer_ru.mp4) | 45.0 s | 1920×1080, 24 fps H264 | 7.8 MB | yes | `26d9cd61c813f7e8…` |
| [`hero_en.mp4`](hero_en.mp4) | 59.5 s | 1920×1080, 24 fps H264 | 17.9 MB | yes | `98b7db9caf357b90…` |
| [`hero_kk.mp4`](hero_kk.mp4) | 59.5 s | 1920×1080, 24 fps H264 | 17.9 MB | yes | `cd6d04bbd399692b…` |
| [`hero_ru.mp4`](hero_ru.mp4) | 59.5 s | 1920×1080, 24 fps H264 | 17.9 MB | yes | `b39a008ea60552c5…` |
| [`teaser_en.mp4`](teaser_en.mp4) | 16.5 s | 1920×1080, 24 fps H264 | 6.4 MB | yes | `6ac7913bb7779411…` |
| [`teaser_kk.mp4`](teaser_kk.mp4) | 16.5 s | 1920×1080, 24 fps H264 | 6.4 MB | yes | `85bb50f355000040…` |
| [`teaser_ru.mp4`](teaser_ru.mp4) | 16.5 s | 1920×1080, 24 fps H264 | 6.4 MB | yes | `4c64a70bb6cb64d3…` |

For the NASA form use **`voiced/demo_en_voice.mp4`** (29.3 s, English, voice-over + music; silent version: `demo_en.mp4`). The other films are for presentations: the form allows at most 30 seconds.
