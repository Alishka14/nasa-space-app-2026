"""Investigation Report: a Markdown rendering of one investigation.

Pure formatting of numbers already in the investigation result; nothing is
computed or interpreted here.
"""
from __future__ import annotations

from typing import Any

from .investigate import f, fp


def render_report(inv: dict[str, Any]) -> str:
    req, region = inv["request"], inv["region"]
    v_info = inv["variables"]
    out = [
        f"# Investigation Report — {region['name']}", "",
        f"*EARTH SENSES {inv['engine_version']} · generated {inv['generated_at']}*", "",
        f"- **Location:** {region['latitude']}, {region['longitude']} "
        f"(grid-cell mean elevation {region.get('grid_cell_elevation_m')} m)",
        f"- **Period:** {req['start']}–{req['end']} · climatological baseline {req['baseline'][0]}–{req['baseline'][1]}",
        f"- **Variables:** " + ", ".join(f"{v_info[v]['label']} [{v_info[v]['display_units']}]" for v in req["variables"]),
        f"- **Data hash:** `{inv['data_hash']}` ({inv['data_source']})", "",
        "## 1. Data provenance", "",
    ]
    for p in inv["provenance"]:
        counts = p["missing_values"]["counts"]
        unused = {k: n for k, n in counts.items() if k not in req["variables"] and n}
        not_used = ("; also in this file but not used: "
                    + ", ".join(f"{k} ({n} missing)" for k, n in unused.items())) if unused else ""
        out += [f"- **Source:** {p['original_source']}",
                f"  - Request: `{p['original_api_request']}`",
                f"  - Retrieved: {p['retrieval_timestamp']} — {p['retrieval_method']}",
                f"  - Product: {p['source_product_version']['api']['name']} {p['source_product_version']['api']['version']}, "
                f"sources {', '.join(p['source_product_version']['sources'])}",
                f"  - Resolution: {p['spatial_resolution']}; {p['temporal_resolution']}",
                f"  - Coverage: {p['coverage']['start']} to {p['coverage']['end']} ({p['coverage']['n_months']} months); "
                f"missing values: {sum(n for k, n in counts.items() if k not in unused)} "
                f"(fill {p['missing_values']['fill_value']}){not_used}",
                f"  - SHA-256: `{p['sha256']}` · validation: {p['validation_status']}"]
    out += ["", "Kind of data: model reanalysis (MERRA-2), not a direct satellite or station measurement.", ""]
    if inv["warnings"]:
        out += ["**Warnings**", ""] + [f"- {w}" for w in inv["warnings"]] + [""]

    out += ["## 2. What is changing, and how fast", "",
            "| Variable | Slope per year (95% CI) | p (autocorrelation-adjusted) | q (FDR) | Verdict |", "|---|---|---:|---:|---|"]
    for v in req["variables"]:
        t = inv["trends"][v]
        s = t["summary"]
        out.append(f"| {v_info[v]['label']} | {f(s['primary_slope'])} ({f(s['primary_ci'][0])} to {f(s['primary_ci'][1])}) "
                   f"{t['slope_units']} | {fp(s['primary_p'])} | {fp(t['q'])} | {t['verdict']} |")
    out.append("")
    for v in req["variables"]:
        t = inv["trends"][v]
        out += [f"**{v_info[v]['label']}.** {t['statement']}", ""]
        if t.get("annual_total"):
            a = t["annual_total"]
            out += [f"Annual accumulation: mean {a['mean']:.0f} {a['units']}; Theil-Sen slope "
                    f"{f(a['summary']['primary_slope'], 2)} {a['slope_units']} "
                    f"(95% CI {f(a['summary']['primary_ci'][0], 2)} to {f(a['summary']['primary_ci'][1], 2)}, "
                    f"p = {fp(a['summary']['primary_p'])}). {a['note']}.", ""]

    if inv["relationships"]:
        out += ["## 3. What varies together", "",
                "| Pair | raw r | seasonal cycle only | deseasonalized r | detrended r (95% CI) | Status | Lag scan |",
                "|---|---:|---:|---:|---|---|---|"]
        for r in inv["relationships"]:
            d = r["detrended"]
            out.append(f"| {r['x']} ↔ {r['y']} | {f(r['raw']['pearson_r'], 2)} | {f(r['seasonal_cycle_only']['pearson_r'], 2)} | "
                       f"{f(r['deseasonalized']['pearson_r'], 2)} | {f(d['pearson_r'], 2)} "
                       f"({f(d['ci95_adjusted'][0], 2)} to {f(d['ci95_adjusted'][1], 2)}) | {r['status']} | {r['lag_verdict']} |")
        out.append("")
        for r in inv["relationships"]:
            out += [f"**{r['x']} ↔ {r['y']}.** {r['statement']}", "", f"{r['lag_statement']}", ""]

    out += ["## 4. Evidence and counterevidence", ""]
    for e in inv["evidence"]:
        if e["claim_type"] == "unverified_physical_explanation":
            continue
        out += [f"### `{e['id']}` · {e['status']} · {e.get('verdict') or ''}", "", e["claim"], ""]
        if e["supporting_evidence"]:
            out += ["Evidence:"] + [f"- {s}" for s in e["supporting_evidence"]] + [""]
        if e["counterevidence"]:
            out += ["Counterevidence:"] + [f"- {s}" for s in e["counterevidence"]] + [""]
        if e.get("alternatives"):
            out += ["Alternatives not excluded:"] + [f"- {s}" for s in e["alternatives"]] + [""]
        if e.get("independent_reports"):
            out += ["Independent reports of the same quantity:"] + [
                f"- {m['metric']}: reported {m['reported']}, ours {m['ours']:.4f} "
                f"({'agrees' if m['agrees'] else 'DISAGREES'}) — {m['source']}" for m in e["independent_reports"]] + [""]

    hyps = [e for e in inv["evidence"] if e["claim_type"] == "unverified_physical_explanation"]
    if hyps:
        out += ["## 5. Hypotheses — proposed, not tested here", "",
                "These are possible explanations. They are not findings."]
        out += [""] + [f"- `{h['id']}` ({' ↔ '.join(h['variables'])}): {h['claim']}" for h in hyps] + [""]

    out += ["## 6. What cannot be concluded from these data", ""] + [f"- {c}" for c in inv["cannot_conclude"]] + [""]
    out += ["## 7. Limitations", ""] + [f"- {c}" for c in inv["limitations"]] + [""]
    rules = inv["decision_rules"]
    out += ["## 8. How to reproduce", "",
            f"Decision rules fixed in advance: alpha = {rules['alpha']}; primary trend test: {rules['trend_primary_test']}; "
            f"{rules['fdr']}; lag scan ±{rules['max_lag']} months; {rules['n_perm']} year-block permutations, seed {rules['seed']}.", "",
            "```bash", "pip install -r backend/requirements.txt",
            "python scripts/build_provenance.py      # re-verifies the SHA-256 of every raw NASA file",
            "python scripts/reproduce_gemini.py      # recomputes the Pavlodar case", "```", "",
            "No language model takes part in any computation in this report.", ""]
    return "\n".join(out)
