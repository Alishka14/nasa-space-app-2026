# EARTH SENSES — Explainer (EXPLAINER_EN)

> Generated from `frontend/src/onboarding/content/intro-scripts.json` · `scripts/build_video_docs.py`. Every number above is filled from facts.json, which is computed by the engine from the NASA files.

| | |
|---|---|
| Variant | EXPLAINER — Explainer |
| Language | English |
| Duration | 45.0 s |
| Target length | 30–45 s |
| Audience | Science fairs, mentors, anyone who wants the finding itself |

## 1. Short concept

One place, one question, one finding — told with the numbers on screen: raw versus deseasonalized correlation, a second pair that shrinks, the limits, and the conclusions the data do not support.

## 2. Scene-by-scene storyboard

| # | Time | Shot | Camera | On-screen text |
|---|---|---|---|---|
| 1 | 0:00.0–0:06.5 | Focus on the grid cell: Globe already close on northern Kazakhstan, marker pulsing at Pavlodar, label and a small caption '288 months · NASA POWER'. | 52.29°, 76.97° · d 2.2 | One place. One question. |
| 2 | 0:06.5–0:13.0 | Correlation bars: Bar chart beside the globe: a blue bar at −0.285 labelled 'raw monthly values', then a longer blue bar at −0.775 labelled 'seasonal cycles alone'. | 52.29°, 76.97° · d 2.6 | Raw: r = −0.285 |
| 3 | 0:13.0–0:19.5 | Correlation flips sign: A third bar grows to the right of zero in red: +0.593, 'seasonal cycle removed'. The contrast with the blue bars is the point of the shot. | 52.29°, 76.97° · d 2.6 | Seasons removed: r = +0.593 |
| 4 | 0:19.5–0:28.0 | Correlation bars: Second pair: a very long blue bar at −0.945 shrinks to −0.316. A small gear icon notes that relative humidity is computed from temperature. | 52.29°, 76.97° · d 2.6 | Temperature ↔ humidity: −0.945 → −0.316 |
| 5 | 0:28.0–0:35.0 | Evidence checklist: Checklist beside the globe with a winter note (December–February r = −0.06) and the line 'correlation ≠ causation'. | 45°, 76.97° · d 2.9 | Correlation ≠ causation |
| 6 | 0:35.0–0:40.5 | Rejected conclusions: The two rejected claims, struck through, each with its number: CI −0.67 to +0.46 °C per decade; q = 0.105. | 45°, 76.97° · d 2.9 | What the data do not support |
| 7 | 0:40.5–0:45.0 | Transition into the app: Dive into the marker and cut to the app's investigation screen. | 52.29°, 76.97° · d 2.35 | Evidence first. |

## 3. Voiceover script

A voiced version with a synthetic voice (ElevenLabs, labelled "AI voice") is in `docs/video/renders/voiced/`; scenes whose line is longer than the scene are slowed there (see `VOICE_TIMING.json`). The in-app intro itself stays silent and shows this narration as subtitles.

**[0:00.0]** Pavlodar, Kazakhstan: 288 months of NASA POWER data. Do precipitation and humidity vary together?  
**[0:06.5]** Raw correlation: −0.285. But the two seasonal cycles alone give −0.775.  
**[0:13.0]** Subtract each month's usual value, and the anomalies correlate at +0.593.  
**[0:19.5]** Temperature and humidity: −0.945 raw, −0.316 without seasons. And relative humidity is partly computed from temperature.  
**[0:28.0]** In winter the link is not detected. And it is a correlation inside one model, not a demonstrated cause.  
**[0:35.0]** “No warming” is not supported. “Humidity is rising” is fragile.  
**[0:40.5]** Every claim comes with its evidence. Open the data.  

## 4. On-screen text

- One place. One question.
- Raw: r = −0.285
- Seasons removed: r = +0.593
- Temperature ↔ humidity: −0.945 → −0.316
- Correlation ≠ causation
- What the data do not support
- Evidence first.
- Before any conclusion: Seasonal cycle removed; Autocorrelation and multiple tests accounted for; Other periods checked; Seasons compared: winter r = −0.06, summer r = +0.70; Correlation ≠ causation; One grid cell, one model (MERRA-2)
- “No warming” — Not supported: the 95% confidence interval runs from −0.67 to +0.46 °C per decade
- “Humidity is rising” — Fragile: q = 0.105 after correction; leaving out one of 5 years flips it
- Data: NASA POWER (MERRA-2 reanalysis) · Pavlodar grid cell · 2001–2024 · Earth imagery: NASA Earth Observatory

## 5. Subtitles

Subtitle file: [`subtitles/explainer_en.srt`](subtitles/explainer_en.srt)

```srt
1
00:00:00,250 --> 00:00:03,527
Pavlodar, Kazakhstan: 288 months of NASA
POWER data.

2
00:00:03,527 --> 00:00:06,300
Do precipitation and humidity vary
together?

3
00:00:06,750 --> 00:00:08,824
Raw correlation: −0.285.

4
00:00:08,824 --> 00:00:12,800
But the two seasonal cycles alone give
−0.775.

5
00:00:13,250 --> 00:00:19,300
Subtract each month's usual value, and the
anomalies correlate at +0.593.

6
00:00:19,750 --> 00:00:23,876
Temperature and humidity: −0.945 raw,
−0.316 without seasons.

7
00:00:23,876 --> 00:00:27,800
And relative humidity is partly computed
from temperature.

8
00:00:28,250 --> 00:00:30,498
In winter the link is not detected.

9
00:00:30,498 --> 00:00:34,800
And it is a correlation inside one model,
not a demonstrated cause.

10
00:00:35,250 --> 00:00:37,694
“No warming” is not supported.

11
00:00:37,694 --> 00:00:40,300
“Humidity is rising” is fragile.

12
00:00:40,750 --> 00:00:43,666
Every claim comes with its evidence.

13
00:00:43,666 --> 00:00:44,800
Open the data.
```

## 6. Estimated duration

- 45.0 s · 7 · 90 words
- Reading speed: 15.9 characters per second, maximum (17)

## 7. Tone direction

Clear and matter-of-fact, like a good lecture slide narrated. Numbers read precisely; no drama.

## 8. Prompt for an external video generator

Shot-by-shot prompts, constraints and sync notes are in [`EXTERNAL_VIDEO_PROMPTS.md`](EXTERNAL_VIDEO_PROMPTS.md#explainer).

