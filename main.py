"""gta6-trophy-rarity-forecast-01 entry (Python 3.13, standard library only).

Forecasts every GTA VI trophy's Exophase earn rate at the case's target as
five quantiles, scored by mean pinball loss on the logit scale.

Model (structural, per trophy):
  A rate is earners / players-tracked. The house's recording shows Exophase
  refreshes its counts on its own schedule: between refreshes the page is
  frozen; at a refresh the tracked-player count jumps and most rates fall
  (new players dilute the pool faster than they earn trophies), while
  earners keep growing as the early cohort progresses. So instead of
  extrapolating the rate directly, this program:
    1. collapses the history into distinct reads (refresh events),
    2. fits log(earners) and log(players) against log-time ln(1 + hours
       since the first read), recency-weighted, per trophy and for the
       player count,
    3. projects both to the target and takes median = earners / players,
    4. shrinks each trophy's projected logit move toward its tier's
       median move (noisy per-trophy fits on 2-decimal rates), and
    5. sets the spread from a random-walk term, the fit residuals, and a
       refresh-jump term (each future refresh can move a rate ~0.5 logit).
  When the history holds too few refreshes to fit, the move falls back to
  a small dilution prior (rates usually fall at a refresh) and the spread
  widens to cover the unseen refreshes. A trophy pinned at 100% in the
  last read stays pinned (the practice recording shows it surviving a 6x
  player jump unchanged).

Everything the program knows at run time is in the case file; the numbers
above are fixed priors, never tuned on any hidden answer.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so `import model` finds a model.py shipped beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]

# Random-walk spread of a rate's move, logit units per square-root day
# (the house baseline's 0.5).
RW_SIGMA = 0.5
# Typical logit move one Exophase refresh inflicts on a rate (the practice
# recording: the baseline's typical miss was ~0.68 logit across a refresh).
REFRESH_MOVE = 0.5
# Dilution prior: expected logit fall per future refresh when the history
# shows no usable drift, and its cap.
PRIOR_PER_REFRESH = 0.12
PRIOR_CAP = 0.5
# Spread floor / cap, logit units.
SPREAD_MIN = 0.35
SPREAD_MAX = 2.2
# Spread of the trophy pinned at 100%.
PINNED_SPREAD = 0.3
# Logit-move caps (rates mostly fall at a refresh; a rise is possible
# where earners outgrow the player count).
MOVE_MIN = -2.0
MOVE_MAX = 1.5


def clamp(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    return math.log(clamp(pct) / (100 - clamp(pct)))


def inv_logit(lg: float) -> float:
    return 100 / (1 + math.exp(-lg))


def round4(x: float) -> float | int:
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value.is_integer() else value


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def wls(xs, ys, ws):
    """Weighted least squares for y ~ a + b*x. Returns (a, b, resid_std)."""
    sw = sum(ws)
    if sw <= 0:
        return None
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    if sxx <= 1e-12:
        return (my, 0.0, 0.0)
    sxy = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
    b = sxy / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    var = sum(w * r * r for w, r in zip(ws, resid)) / sw
    return (a, b, math.sqrt(var))


def distinct_reads(history):
    """Collapse consecutive identical reads (frozen page between refreshes)."""
    out = []
    prev = None
    for r in history:
        key = (r.get("players_tracked"), tuple(r.get("rates") or []))
        if key != prev:
            out.append(r)
            prev = key
    return out


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    history = case.get("history") or []
    if not history:
        raise ValueError(f"{name} has no history")
    trophies = case["trophies"]
    horizon_days = case["horizon_minutes"] / 1440.0

    reads = distinct_reads(history)
    t0 = parse_time(reads[0]["at"])
    # Log-time in hours since the first read; the target in the same units.
    t_last = parse_time(reads[-1]["at"])
    x_target = math.log1p((t_last - t0).total_seconds() / 3600.0 + case["horizon_minutes"] / 60.0)
    xs = []
    for r in reads:
        t = parse_time(r["at"])
        xs.append(math.log1p((t - t0).total_seconds() / 3600.0))
    # Recency weights: half-life 24 h.
    t_last_h = (t_last - t0).total_seconds() / 3600.0
    ws = []
    for r in reads:
        t = (parse_time(r["at"]) - t0).total_seconds() / 3600.0
        ws.append(0.5 ** ((t_last_h - t) / 24.0))

    # Players-tracked fit (log count vs log-time).
    p_counts = [max(1, r.get("players_tracked") or 1) for r in reads]
    log_p = [math.log(p) for p in p_counts]
    fit_p = wls(xs, log_p, ws) if len(reads) >= 3 else None
    refreshes_per_day = max(1.0, (len(reads) - 1) / max(0.25, t_last_h / 24.0)) if len(reads) >= 2 else 1.0
    expected_refreshes = min(6.0, max(0.5, refreshes_per_day * horizon_days))
    p_last = p_counts[-1]
    if fit_p is not None:
        p_proj = math.exp(fit_p[0] + fit_p[1] * x_target)
        p_proj = min(max(p_proj, p_last * 0.5), p_last * 50.0)
        p_resid = fit_p[2]
    else:
        p_proj = float(p_last)
        p_resid = 0.0

    # Per-trophy earner fits.
    moves = []
    infos = []
    for i, trophy in enumerate(trophies):
        last_rate = reads[-1]["rates"][i]
        if last_rate is None:
            last_rate = 0.0
        # Earners in each distinct read (pseudo-count keeps log finite).
        e_vals = []
        ok = True
        for r in reads:
            rate = r["rates"][i]
            if rate is None:
                ok = False
                break
            e_vals.append(max(rate * (r.get("players_tracked") or 1) / 100.0, 0.5))
        fit_e = wls(xs, [math.log(e) for e in e_vals], ws) if ok and len(reads) >= 3 else None
        if fit_e is not None:
            e_proj = math.exp(fit_e[0] + fit_e[1] * x_target)
            e_proj = min(max(e_proj, 0.25), p_proj)  # earners cannot exceed players
            median = 100.0 * e_proj / p_proj
            move = logit(median) - logit(last_rate)
            e_resid = fit_e[2]
        else:
            median = last_rate
            move = 0.0
            e_resid = 0.0
        infos.append({
            "last": last_rate, "median": median, "move": move,
            "e_resid": e_resid, "tier": trophy.get("tier"),
        })
        moves.append(move)

    # Shrink each move toward its tier's median move (weight by how much
    # the history actually says: more refresh events -> trust the fit).
    w_data = min(1.0, max(0.0, (len(reads) - 1) / 4.0))
    tiers: dict[str, list[float]] = {}
    for info in infos:
        tiers.setdefault(str(info["tier"]), []).append(info["move"])
    all_moves = sorted(moves)
    med_all = all_moves[len(all_moves) // 2]
    tier_med = {}
    for tier, ms in tiers.items():
        s = sorted(ms)
        tier_med[tier] = s[len(s) // 2] if len(s) >= 3 else med_all
    prior_move = -min(PRIOR_CAP, PRIOR_PER_REFRESH * expected_refreshes)

    rows = []
    for i, trophy in enumerate(trophies):
        info = infos[i]
        last_rate = info["last"]
        if last_rate >= 99.9:
            # Pinned at (near) 100%: the practice recording shows it
            # surviving a 6x player jump unchanged.
            median = 99.99
            spread = PINNED_SPREAD
        else:
            fitted = info["move"]
            shrunk = 0.5 * fitted + 0.5 * tier_med.get(str(info["tier"]), med_all)
            move = w_data * shrunk + (1.0 - w_data) * prior_move
            move = min(MOVE_MAX, max(MOVE_MIN, move))
            median = inv_logit(logit(last_rate) + move)
            median = clamp(median)
            s_rw = RW_SIGMA * math.sqrt(horizon_days)
            s_fit = min(1.0, math.sqrt(info["e_resid"] ** 2 + p_resid ** 2))
            s_ref = REFRESH_MOVE * math.sqrt(expected_refreshes)
            spread = math.sqrt(s_rw ** 2 + s_fit ** 2 + s_ref ** 2)
            spread = min(SPREAD_MAX, max(SPREAD_MIN, spread))
        lg = logit(median)
        qs = []
        prev_q = -1.0
        for z in Z:
            q = round4(inv_logit(lg + z * spread))
            q = float(q)
            if q < prev_q:
                q = prev_q
            qs.append(q)
            prev_q = q
        rows.append({"id": trophy["id"], "q": qs})
    return {"trophies": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
