# bio-reasoning-2026 — dev tasks. `make verify` is the fast loop signal read.
.PHONY: verify

VAL_N ?= 80
MAX_TRIALS ?= 6
PROPOSER ?= grid

# Fast dev verification: preflight the loop (assert it's healthy), then a cheap
# subsample search that prints baseline vs best-variant mean (signal ⇒ escalate to
# a full-val run / throughput-opt; near-chance ⇒ file a negative-result finding).
# DEV-ONLY: the val_n subsample makes the gate UNtrustworthy — never promote off it.
verify:
	uv run python scripts/verify_loop.py --val-n $(VAL_N)
	uv run python scripts/self_improve_loop.py --val-n $(VAL_N) \
		--proposer $(PROPOSER) --max-trials $(MAX_TRIALS)
