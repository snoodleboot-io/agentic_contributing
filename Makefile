PYTHON ?= python3
VALIDATOR := $(PYTHON) tools/validate_agentic_contributing.py

.PHONY: verify lint test check-template check-examples help

help:
	@echo "make lint            validate this repository's own AGENTIC_CONTRIBUTING.md (strict)"
	@echo "make check-examples  validate the worked example (strict)"
	@echo "make check-template  validate the template (placeholders allowed)"
	@echo "make test            run the validator test suite"
	@echo "make verify          lint + check-examples + test"

lint:
	$(VALIDATOR) --strict AGENTIC_CONTRIBUTING.md

check-template:
	$(VALIDATOR) templates/AGENTIC_CONTRIBUTING.template.md

check-examples:
	$(VALIDATOR) --strict examples/AGENTIC_CONTRIBUTING.example.md

test:
	$(PYTHON) -m unittest discover -s tools -p 'test_*.py' -v

verify: lint check-examples test
