# gta6-trophy-forecast

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/swchiguge1-forge/gta6-trophy-forecast/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/swchiguge1-forge/gta6-trophy-forecast/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

A program that reads one case file (the house's recording of Exophase's
GTA VI PS5 trophy page) and forecasts every trophy's earn rate at the
case's target as five quantiles, scored by mean pinball loss on the logit
scale. A rate is earners / players-tracked, and Exophase refreshes its
counts on its own schedule: at a refresh the tracked player count jumps
and most rates fall, because new players dilute the pool faster than they
earn trophies. So instead of extrapolating the rate, the program fits
log(earners) and log(players) against log-time, projects both to the
target, and takes median = earners / players, with a spread from a
random-walk term, the fit residuals, and a refresh-jump term.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=g9gpq3bv&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
