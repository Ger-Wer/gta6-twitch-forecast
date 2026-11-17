# gta6-twitch-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Ger-Wer/gta6-twitch-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Ger-Wer/gta6-twitch-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

An hour-by-hour forecast of Grand Theft Auto VI's launch-day Twitch viewers, built from the launch-day shapes of 42 past big game launches, anchored on the first hour's count.

## How it works

Every past launch in the case has a release-day hourly curve. Divide each curve by its own hour-1 print and you get a log-ratio shape for hours 2–24. The shape depends strongly on how big hour 1 already is: a small hour 1 means the launch has barely started anywhere (its evening peak can be hundreds of times hour 1), a huge hour 1 means most of the world is already watching (its peak barely clears hour 1). So for each forecast hour the program fits a local line of log-ratio against log hour-1 over the 18 comparables nearest in log hour-1, and reads the fit at this case's hour 1. The spread comes from the residuals' MAD, widened into the five scored quantiles.

On the four practice launches it scores a mean pinball loss of 0.191 in log space (typical miss about 35%), against 0.387 for the house's flat baseline — and it stays sane at GTA scale, where the predicted evening peak sits near hour 1, as it did for Elden Ring and Cyberpunk 2077.

## Run it

```sh
python3 main.py
```

The program reads every `*.in` case from `$MAKEFUN_INPUT_DIR` (or `/input`) and writes one `*.out` forecast per case to `$MAKEFUN_OUTPUT_DIR` (or `/output`). Python 3.13, standard library only, no network, deterministic: the same case always gives the same bytes.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
