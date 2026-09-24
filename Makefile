PY ?= python3
VENV := .venv
PYTEST := $(VENV)/bin/pytest

.PHONY: setup test try clean

$(PYTEST):
	$(PY) -m venv $(VENV)
	$(VENV)/bin/pip install -q pytest

setup: $(PYTEST)

# Run every chip's tests against the reference solutions.
test: $(PYTEST)
	$(PYTEST)

# Run one chip's tests against YOUR starter.py:
#   make try CHIP=01-observability/DC-OBS-01-metric-lookup
try: $(PYTEST)
	@test -n "$(CHIP)" || (echo "usage: make try CHIP=<track>/<chip-folder>" && exit 1)
	CHIP_TARGET=starter $(PYTEST) $(CHIP)

clean:
	rm -rf $(VENV) .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
