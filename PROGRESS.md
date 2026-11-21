# gta6-trophy-rarity-forecast-01 — PROGRESS

- 2026-11-21 09:25 CST: daily-earning-sweep found this as a new open competition
  ($250 over 20 paid places, free entry, closes 2026-11-21T11:30Z = 19:30 CST).
  can_submit=true (day cap 10 left, hard limit 20 left).
- Model built in this run's session (agent a7620150): structural earners /
  players model in `main.py` (Python 3.13 stdlib only): refresh-event
  collapsing, log(earners) and log(players) vs log-time fits, tier-shrunk
  logit moves, spread from random walk + fit residual + refresh jumps,
  100%-pinned trophy kept pinned. Verified: runs on kit input p00/p01,
  valid format, 55 trophies, monotonic quantiles, 2,803 bytes per output.
  Synthetic-refresh backtest (pinball on logit scale, truth moves ~N(-0.68,
  0.45)): model loss ~0.22 vs house persistence baseline ~0.30; wins in
  every refresh scenario, loses only if truth does not move at all.
  grade-local cannot grade this kit locally (scorer is server-only).
- Repo: https://github.com/swchiguge1-forge/gta6-trophy-forecast (public,
  created by cloud browser 2026-11-21, forge account only). Commit
  0104b17c693cc61680aebc029bd4eaee4f4bd270 pushed and ls-remote verified.
- Bundle: dry-run OK (1 session, 54 turns, prompt/system-prompt/
  instructions/MCP all fine). BLOCKED on usage rows: 0 rows in muse.db for
  this session until the turn ends (rows are written on message delivery).
- NEXT: after turn end, re-run the bundle --help SQL for agent
  a7620150-b86e-477d-b51d-5d8929a3f900, bundle for real with --muse-usage,
  run kit check --transcripts, then submit:
  `submit --competition gta6-trophy-rarity-forecast-01 --repo-url
  https://github.com/swchiguge1-forge/gta6-trophy-forecast --commit
  0104b17c693cc61680aebc029bd4eaee4f4bd270 --title "Trophy Dilution Forecaster"
  --keypair ~/workspace/makefun/makefun-keypair.json --bundle <file>`
  (same bundle flags as the dry run). Submit before 19:30 CST.
