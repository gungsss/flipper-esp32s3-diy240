#!/usr/bin/env python3
"""M4145 offline RF resilience experiment: deterministic packet-loss simulation.

This is an offline test harness, not an RF transmitter. Python stdlib only.
"""
import argparse
import csv
import json
import random
from pathlib import Path

def simulate(packets: int, baseline_loss: float, interference_loss: float, seed: int):
    rng = random.Random(seed)
    results = []
    for i in range(packets):
        phase = "baseline" if i < packets // 2 else "interference"
        probability = baseline_loss if phase == "baseline" else interference_loss
        delivered = rng.random() >= probability
        latency_ms = round(rng.uniform(3.0, 8.0) + (rng.uniform(0, 20) if phase == "interference" else 0), 3) if delivered else None
        results.append(dict(sequence=i, phase=phase, delivered=int(delivered), latency_ms=latency_ms))
    return results

def summarize(rows):
    out = {}
    for phase in ("baseline", "interference"):
        selected = [r for r in rows if r["phase"] == phase]
        received = [r for r in selected if r["delivered"]]
        out[phase] = {
            "sent": len(selected),
            "received": len(received),
            "packet_loss_pct": round(100 * (len(selected) - len(received)) / len(selected), 2) if selected else None,
            "mean_latency_ms": round(sum(r["latency_ms"] for r in received) / len(received), 3) if received else None,
        }
    return out

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=int, default=200)
    parser.add_argument("--baseline-loss", type=float, default=0.01)
    parser.add_argument("--interference-loss", type=float, default=0.30)
    parser.add_argument("--seed", type=int, default=4145)
    parser.add_argument("--output", type=Path, default=Path("rf_resilience.csv"))
    args = parser.parse_args()
    if args.packets < 2 or args.packets % 2:
        parser.error("--packets must be even and >= 2")
    if not all(0 <= p <= 1 for p in (args.baseline_loss, args.interference_loss)):
        parser.error("loss probabilities must be between 0 and 1")
    rows = simulate(args.packets, args.baseline_loss, args.interference_loss, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["sequence", "phase", "delivered", "latency_ms"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"mode": "offline-simulation", "seed": args.seed, "summary": summarize(rows), "csv": str(args.output)}, indent=2))

if __name__ == "__main__":
    main()
