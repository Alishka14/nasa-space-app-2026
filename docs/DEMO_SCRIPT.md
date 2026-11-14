# Demo Script

A walk-through of about four minutes, plus a 30-second cut. Every number below is what the tool shows for the bundled
Pavlodar data; check the current Space Apps rules for the allowed length and format of the project demo.

**Before you start:** `uvicorn earth_senses.api:app --app-dir backend --port 8000` with the frontend built
(`cd frontend && npm run build`), browser at <http://localhost:8000>. For a demo without internet set
`EARTH_SENSES_OFFLINE=1`; Pavlodar and Almaty work from bundled NASA files.

## Four-minute version

| Time | Do | Say |
|---|---|---|
| 0:00 | Show the start screen with the map. | "The challenge asks for a trend detective. Finding a trend is easy. Knowing whether to believe it is the hard part, so we built a tool that investigates and keeps the evidence." |
| 0:20 | Click **Pavlodar**. Point at the rectangle on the map. | "This is real NASA data: MERRA-2 through the POWER service. A point is really a grid cell, about fifty kilometres across, and we show that instead of hiding it." |
| 0:35 | Keep temperature, humidity and precipitation ticked, 2001–2024. Click **Investigate**. | "Three variables, twenty-four years." |
| 0:45 | Trend cards. | "Temperature: minus 0.02 degrees per year, not significant. The tool does not say 'no warming'. It says a record this short could only detect trends above 0.9 degrees per decade." |
| 1:10 | Humidity card, then the heatmap with RH2M selected. | "Humidity looks significant: p = 0.035. But after correcting for three tests it is 0.105, it flips if you remove any one of five years, and over 1981–2024 it is gone. Verdict: fragile." |
| 1:40 | Scroll to *Air temperature ↔ Relative humidity*. Point at the four bars. | "Raw correlation minus 0.95. The two seasonal cycles alone give minus 0.98. Between anomalies it is minus 0.32. Most of that famous number was the calendar." |
| 2:00 | *Precipitation ↔ Relative humidity*. | "Here the sign changes: minus 0.28 raw, plus 0.59 once the seasons are removed." |
| 2:15 | *Air temperature ↔ Precipitation*, season chart. | "And here the all-year number hides opposite behaviour: plus 0.37 in winter, minus 0.32 in summer." |
| 2:30 | Click **View evidence** on a relationship. Scroll the drawer. | "Every result has a record: the claim, the evidence, the counterevidence, alternatives we could not exclude, limitations, and the NASA file with its SHA-256." |
| 2:50 | Tab **Relationship graph**. | "An edge exists only if it was computed from data. Hypotheses are dashed notes on an edge and can never create one." |
| 3:05 | In **Try the MIZAN Guard** click **Check wording**. | "If anyone, human or AI, writes 'temperature causes humidity to fall, which proves the link', it is blocked." |
| 3:20 | Tab **Evidence timeline**. | "This is how each interpretation was reached and revised: observation, hypothesis, test, counterexample, revision, conclusion." |
| 3:35 | Tab **Compare regions**, Pavlodar vs Almaty, **Compare**. | "Same variable, two places, opposite signs, neither significant, and the tool says exactly that. It also warns that this 'Almaty' cell sits at 2,500 metres." |
| 3:50 | Tab **Report**. | "One click gives the full report, ending with what cannot be concluded. AI proposes. Evidence decides." |

## Thirty-second version

1. (0–8 s) Map → Pavlodar → Investigate. "Real NASA data, one click."
2. (8–18 s) The four correlation bars for temperature–humidity. "−0.95 raw. −0.32 once the seasons are removed."
3. (18–25 s) View evidence drawer. "Every number has evidence, counterevidence and a NASA file hash."
4. (25–30 s) Guard blocks the causal sentence. "And it will not let you overclaim."

## Questions a judge may ask

| Question | Answer |
|---|---|
| Is this NASA data from the Resources tab? | Not yet. It is MERRA-2, which the challenge names, obtained through NASA POWER. Retrieval through a listed tool is the first open item (`KNOWN_LIMITATIONS.md`). |
| Did an AI make the conclusions? | No. All numbers come from deterministic code on hashed data. AI wrote the code and a first analysis; the tests and the evidence records are what the results rest on. |
| How do you know the statistics are right? | Cross-checked against `pymannkendall` and `statsmodels`, against synthetic series with known answers, and against Gemini's independent numbers. |
| Why is "no significant trend" not "no change"? | The confidence interval for temperature runs from −0.67 to +0.46 °C per decade. |
| What does "values replicated" mean? | Those numbers were also obtained by a second, independent assessor from separately retrieved NASA data. The finding as a whole stays OBSERVED. |
