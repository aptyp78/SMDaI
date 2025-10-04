.PHONY: pipeline-mini eval

PYTHON ?= python3

pipeline-mini:
	$(PYTHON) eval/compute_baseline.py

eval:
	$(PYTHON) eval/skeptic_check.py --baseline eval/baseline.json --metrics eval/metrics.json --report eval/report.md
	@echo "Report → eval/report.md"
