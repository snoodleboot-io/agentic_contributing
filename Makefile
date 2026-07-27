PYTHON ?= python3
VALIDATOR := $(PYTHON) tools/validate_agentic_contributing.py

.PHONY: verify lint test check-template help

help:
	@echo "make lint      validate this repository's own AGENTIC_CONTRIBUTING.md (strict)"
	@echo "make test      run the validator test suite"
	@echo "make verify    lint + test"

lint:
	$(VALIDATOR) --strict AGENTIC_CONTRIBUTING.md

check-template:
	$(VALIDATOR) templates/AGENTIC_CONTRIBUTING.template.md

test:
	$(PYTHON) -m unittest discover -s tools -p 'test_*.py' -v

verify: lint test
