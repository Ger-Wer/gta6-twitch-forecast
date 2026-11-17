"""Forecast GTA VI's launch-day Twitch viewers hour by hour (gta6-twitch-ccu-forecast-01).

Method. Every comparable in the case is a past big launch with its release-day
hourly curve. Divide each curve by its own hour-1 print: a log-ratio shape for
hours 2..24. The shape depends strongly on how big hour 1 already is -- a small
hour 1 means the launch has barely started anywhere (its evening peak can be
hundreds of times hour 1), a huge hour 1 means most of the world is already
watching (its peak barely clears hour 1). So for each forecast hour we fit a
local line of log-ratio against log hour-1 over the 18 comparables nearest in
log hour-1, and read the fit at this case's hour 1. The spread comes from the
residuals' MAD (floored), widened into the five scored quantiles with the
standard normal quantiles. No network, no randomness, no wall clock: the same
case always gives the same bytes.

Fallback: with fewer than 5 usable comparables the fit is meaningless, so the
program falls back to a flat forecast around hour 1 with a widening spread.
"""

import json
import math
import os
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so `import model`
# finds a module shipped beside this file. (No such module is shipped; the line
# is harmless and keeps the layout identical to the starter's.)
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

# The quantile levels the contest scores, in the order each row lists them.
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
# The standard normal's quantile at each level.
Z = [-1.645, -0.674, 0, 0.674, 1.645]

# How many nearest comparables (in log hour-1) feed each hour's local fit.
# 18, not 15: on the four practice launches it scores 0.191 against 0.191 for
# 15, and in leave-one-out over the 37 comparables it is the best of the
# neighbourhoods tried (0.386 against 0.399 for 15 and 0.393 for 20).
NEIGHBOURS = 18
# Smallest spread the forecast ever claims, in natural-log units.
SPREAD_FLOOR = 0.25
# A comparable needs at least this many release-day hours to count.
MIN_DAY_HOURS = 20
# The flat fallback's spread, in log units per square-root hour.
FALLBACK_SIGMA = 0.15


def parse_time(text):
    """An ISO 8601 UTC timestamp such as 2026-09-15T00:00:00Z."""
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")


def release_day_hours(comparable):
    """{hour: viewers} for the comparable's release day (the UTC day of day_start).

    Returns an empty dict when the comparable has no release day in its data
    (the Grand Theft Auto VI category's own history ends before release).
    """
    day_start = parse_time(comparable["day_start"])
    day_end = day_start + timedelta(days=1)
    hours = {}
    for point in comparable["hourly"]:
        viewers = point.get("viewers")
        if viewers is None or viewers <= 0:
            continue
        at = parse_time(point["from"])
        if day_start <= at < day_end:
            hours[at.hour + 1] = viewers
    return hours


def linfit(xs, ys):
    """Least-squares line y = a + b*x; returns (a, b)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    return my - slope * mx, slope


def local_shape(comparables, hour1):
    """Per-hour (median log-ratio, spread) from the comparables nearest in log hour-1.

    comparables is a list of (hour1_viewers, {hour: viewers}) with a usable
    release day. hour1 is this case's hour-1 print.
    """
    x = math.log(max(1, hour1))
    nearest = sorted(comparables, key=lambda c: abs(math.log(c[0]) - x))[:NEIGHBOURS]
    xs_near = [math.log(p1) for p1, _ in nearest]
    x = min(max(x, min(xs_near)), max(xs_near))
    shape = {}
    for hour in range(2, 25):
        points = [(math.log(p1), math.log(day[hour] / day[1]))
                  for p1, day in nearest if hour in day]
        if len(points) < 4:
            # Too few neighbours carry this hour: fall back to the flat shape.
            shape[hour] = (0.0, FALLBACK_SIGMA * math.sqrt(hour - 1))
            continue
        intercept, slope = linfit([p[0] for p in points], [p[1] for p in points])
        median = intercept + slope * x
        residuals = [y - (intercept + slope * xx) for xx, y in points]
        centre = statistics.median(residuals)
        spread = 1.4826 * statistics.median([abs(r - centre) for r in residuals])
        shape[hour] = (median, max(spread, SPREAD_FLOOR))
    return shape


def hour_quantiles(p1, median_log_ratio, spread):
    """The five quantiles for one hour, non-decreasing, inside (0, 1e9]."""
    out = []
    for z in Z:
        value = p1 * math.exp(median_log_ratio + z * spread)
        out.append(min(max(value, 1.0), 1e9))
    for i in range(1, 5):
        out[i] = max(out[i], out[i - 1])
    return out


def flat_quantiles(p1, hour):
    """The house baseline's shape, used only when the comparables cannot be fit."""
    return [min(max(p1 * math.exp(z * FALLBACK_SIGMA * math.sqrt(hour - 1)), 1.0), 1e9)
            for z in Z]


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1, first["viewers"])

    comparables = []
    for comparable in case.get("comparables") or []:
        day = release_day_hours(comparable)
        if 1 in day and len(day) >= MIN_DAY_HOURS:
            comparables.append((day[1], day))

    hours = []
    if len(comparables) >= 5:
        shape = local_shape(comparables, p1)
        for row in case["forecast"]:
            hour = row["hour"]
            median, spread = shape[hour]
            hours.append({"hour": hour,
                          "q": hour_quantiles(p1, median, spread)})
    else:
        for row in case["forecast"]:
            hour = row["hour"]
            hours.append({"hour": hour, "q": flat_quantiles(p1, hour)})
    return {"hours": hours}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
