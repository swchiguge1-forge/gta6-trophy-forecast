# GTA VI Trophy Rarity Forecast

Entry for make.fun `gta6-trophy-rarity-forecast-01`: a program that reads one
case file (the house's recording of Exophase's GTA VI PS5 trophy page) and
forecasts every trophy's earn rate at the case's target as five quantiles,
scored by mean pinball loss on the logit scale.

## Model

A rate is earners / players-tracked, and Exophase refreshes its counts on its
own schedule: between refreshes the page is frozen; at a refresh the tracked
player count jumps and most rates fall, because new players dilute the pool
faster than they earn trophies. So instead of extrapolating the rate, the
program (`main.py`, Python 3.13, standard library only):

1. collapses the history into distinct reads (refresh events),
2. fits log(earners) and log(players) against log-time, recency-weighted,
3. projects both to the target and takes median = earners / players,
4. shrinks each trophy's projected logit move toward its tier's median move,
5. sets the spread from a random-walk term, the fit residuals, and a
   refresh-jump term. A trophy pinned at 100% stays pinned.

## Run

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## License

MIT — see LICENSE.
