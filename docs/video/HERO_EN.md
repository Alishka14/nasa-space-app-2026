# EARTH SENSES — Full film (HERO_EN)

> Generated from `frontend/src/onboarding/content/intro-scripts.json` · `scripts/build_video_docs.py`. Every number above is filled from facts.json, which is computed by the engine from the NASA files.

| | |
|---|---|
| Variant | HERO — Full film |
| Language | English |
| Duration | 59.5 s |
| Target length | 45–60 s |
| Audience | Judges, presentations, the opening of a demo |

## 1. Short concept

From the whole living planet down to one grid cell, then a reversal: the same NASA data give a negative and a positive correlation. The film ends on the method — evidence, limits, no causal shortcuts — and hands the viewer the tool.

## 2. Scene-by-scene storyboard

| # | Time | Shot | Camera | On-screen text |
|---|---|---|---|---|
| 1 | 0:00.0–0:06.0 | Earth from space: Slow push-in on a photoreal Earth from deep space, day side lit from the left, night side with city lights on the right, thin blue atmospheric rim. Stars sharp and sparse. No text. | 25°, 40° · d 3.6 | EARTH SENSES |
| 2 | 0:06.0–0:12.5 | Data layers over the globe: The globe takes on a cool analytical tint; glowing cyan coastlines and a faint latitude-longitude grid fade in. Three labelled data layers (temperature orange, humidity green, precipitation blue) shimmer across Central Asia. | 42°, 66° · d 3.0 | Air, water and heat change together. |
| 3 | 0:12.5–0:19.0 | Focus on the grid cell: Camera glides to northern Kazakhstan and settles on a single pulsing marker at 52.3°N 77.0°E with a short light beam rising from the surface. A thin label reads 'Pavlodar'. | 52.29°, 76.97° · d 2.15 | Pavlodar, Kazakhstan · 2001–2024 |
| 4 | 0:19.0–0:27.0 | Raw time series: The globe slides left. On the right, two monthly time series (precipitation in blue, relative humidity in green) draw themselves across 24 years; they swing in opposite directions every year. A correlation value appears: r = −0.285. | 52.29°, 76.97° · d 2.6 | At first glance, the data say one thing… |
| 5 | 0:27.0–0:35.0 | Correlation flips sign: A horizontal bar anchored at zero shows −0.285 in blue; it swings smoothly through zero and grows to +0.593 in red while the two curves re-draw as anomalies that now rise and fall together. | 52.29°, 76.97° · d 2.6 | Remove the seasons: r = +0.593 |
| 6 | 0:35.0–0:40.5 | Title over the globe: Wide shot, the globe turning slowly. One line of white text in the centre. Breathing room — no graphics. | 40°, 70° · d 3.1 | Seasonality changed the interpretation. |
| 7 | 0:40.5–0:47.5 | Evidence checklist: A clean checklist appears line by line beside the globe: seasonal cycle removed; autocorrelation and multiple tests accounted for; other periods checked; correlation is not causation. Each line gets a small cyan tick. | 45°, 76.97° · d 2.9 | EARTH SENSES investigates relationships, evidence and uncertainty. |
| 8 | 0:47.5–0:55.0 | Rejected conclusions: Two short claims appear in quotation marks and are struck through: 'No warming' (with its confidence interval −0.67 to +0.46 °C per decade) and 'Humidity is rising' (marked fragile). Restrained, factual typography. | 45°, 76.97° · d 2.9 | It also shows what the data cannot support. |
| 9 | 0:55.0–0:59.5 | Transition into the app: The camera dives toward the marker; the frame dissolves into the dark interface of the EARTH SENSES app with its map and charts. | 52.29°, 76.97° · d 2.35 | Investigate for yourself. |

## 3. Voiceover script

A voiced version with a synthetic voice (ElevenLabs, labelled "AI voice") is in `docs/video/renders/voiced/`; scenes whose line is longer than the scene are slowed there (see `VOICE_TIMING.json`). The in-app intro itself stays silent and shows this narration as subtitles.

**[0:00.0]** This is one planet — and one connected system.  
**[0:06.0]** Air, water and heat change together, month after month, all over the planet.  
**[0:12.5]** We followed one place for twenty-four years: Pavlodar, in NASA POWER data.  
**[0:19.0]** At first glance, months with more precipitation have lower humidity: r = −0.285.  
**[0:27.0]** Remove the seasonal cycle and the sign flips: +0.593. Wetter-than-usual months are also more humid than usual.  
**[0:35.0]** The first number described the calendar, not the weather.  
**[0:40.5]** EARTH SENSES tests every relationship, keeps the evidence, and does not mistake correlation for cause.  
**[0:47.5]** “No warming” is not a valid conclusion here, and “humidity is rising” is a fragile result.  
**[0:55.0]** Now, investigate for yourself.  

## 4. On-screen text

- EARTH SENSES
- Air, water and heat change together.
- Pavlodar, Kazakhstan · 2001–2024
- At first glance, the data say one thing…
- Remove the seasons: r = +0.593
- Seasonality changed the interpretation.
- EARTH SENSES investigates relationships, evidence and uncertainty.
- It also shows what the data cannot support.
- Investigate for yourself.
- Before any conclusion: Seasonal cycle removed; Autocorrelation and multiple tests accounted for; Other periods checked; Seasons compared: winter r = −0.06, summer r = +0.70; Correlation ≠ causation; One grid cell, one model (MERRA-2)
- “No warming” — Not supported: the 95% confidence interval runs from −0.67 to +0.46 °C per decade
- “Humidity is rising” — Fragile: q = 0.105 after correction; leaving out one of 5 years flips it
- Data: NASA POWER (MERRA-2 reanalysis) · Pavlodar grid cell · 2001–2024 · Earth imagery: NASA Earth Observatory

## 5. Subtitles

Subtitle file: [`subtitles/hero_en.srt`](subtitles/hero_en.srt)

```srt
1
00:00:00,250 --> 00:00:05,800
This is one planet — and one connected
system.

2
00:00:06,250 --> 00:00:12,300
Air, water and heat change together, month
after month, all over the planet.

3
00:00:12,750 --> 00:00:18,800
We followed one place for twenty-four
years: Pavlodar, in NASA POWER data.

4
00:00:19,250 --> 00:00:26,800
At first glance, months with more precipitation
have lower humidity: r = −0.285.

5
00:00:27,250 --> 00:00:30,921
Remove the seasonal cycle and the sign
flips: +0.593.

6
00:00:30,921 --> 00:00:34,800
Wetter-than-usual months are also more
humid than usual.

7
00:00:35,250 --> 00:00:40,300
The first number described the calendar,
not the weather.

8
00:00:40,750 --> 00:00:44,511
EARTH SENSES tests every relationship,
keeps the evidence,

9
00:00:44,511 --> 00:00:47,300
and does not mistake correlation for
cause.

10
00:00:47,750 --> 00:00:51,235
“No warming” is not a valid conclusion
here,

11
00:00:51,235 --> 00:00:54,800
and “humidity is rising” is a fragile
result.

12
00:00:55,250 --> 00:00:59,300
Now, investigate for yourself.
```

## 6. Estimated duration

- 59.5 s · 9 · 108 words
- Reading speed: 15.4 characters per second, maximum (17)

## 7. Tone direction

Calm, confident, cinematic. A documentary narrator, not a trailer voice. Let the numbers land; pause after the flip.

## 8. Prompt for an external video generator

Shot-by-shot prompts, constraints and sync notes are in [`EXTERNAL_VIDEO_PROMPTS.md`](EXTERNAL_VIDEO_PROMPTS.md#hero).

