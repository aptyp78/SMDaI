#!/usr/bin/env python3
import argparse, json, sys, math, pathlib

def flatten(prefix, obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(f"{prefix}{k}.", v, out)
    else:
        out[prefix[:-1]] = obj
    return out

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    base = load_json(args.baseline)
    met = load_json(args.metrics)
    met_flat = flatten("", met, {}) if isinstance(met, dict) else met

    rows = []
    failed = False
    for k, min_val in base.items():
        actual = met_flat.get(k)
        if actual is None:
            rows.append((k, min_val, "—", "MISSING", "❌"))
            failed = True
            continue
        try:
            a = float(actual)
            delta = a - float(min_val)
            ok = a >= float(min_val)
            rows.append((k, min_val, a, f"{delta:+.3f}", "✅" if ok else "❌"))
            if not ok:
                failed = True
        except Exception:
            rows.append((k, min_val, actual, "N/A", "❌"))
            failed = True

    report = ["# Skeptic report", "", "| metric | baseline | actual | Δ | pass |", "|---|---:|---:|---:|:---:|"]
    for k, b, a, d, p in rows:
        report.append(f"| `{k}` | {b} | {a} | {d} | {p} |")
    pathlib.Path(args.report).write_text("\n".join(report), encoding="utf-8")

    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
