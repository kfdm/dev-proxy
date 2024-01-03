SYSTEM_PYTHON ?= python3.11
VENV_DIR := .venv
PYTHON_BIN := $(VENV_DIR)/bin/python
APP_BIN := $(VENV_DIR)/bin/dev-server
RUFF_BIN := $(VENV_DIR)/bin/ruff
BLACK_BIN := $(VENV_DIR)/bin/black


.PHONY: format
format: $(RUFF_BIN) 
	$(RUFF_BIN) check  --fix .
	$(RUFF_BIN) format .

################################################################################
# Internal Commands
################################################################################
$(VENV_DIR):
	$(SYSTEM_PYTHON) -m venv $(VENV_DIR)

$(PYTHON_BIN): $(VENV_DIR)

$(APP_BIN): $(VENV_DIR)
	$(PYTHON_BIN) -m pip install -e .

$(RUFF_BIN): $(PYTHON_BIN)
	$(PYTHON_BIN) -m pip install ruff


################################################################################
# Dev Commands
################################################################################

.PHONY: pip
pip: $(PYTHON_BIN)
	$(PYTHON_BIN) -m pip install -e .

.PHONY: web
web: $(APP_BIN)
	$(APP_BIN) web --port 7999

.PHONY: install
install: $(APP_BIN)
	$(APP_BIN) install
