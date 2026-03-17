# ----------------------------------------
# CloudMatchAI Job Scraper Makefile
# ----------------------------------------

PYTHON := python3
VENV := env
ACTIVATE := source $(VENV)/bin/activate

# Default target
all: install

# ----------------------------------------
# Create virtual environment
# ----------------------------------------
venv:
    $(PYTHON) -m venv $(VENV)

# ----------------------------------------
# Install dependencies
# ----------------------------------------
install: venv
    $(ACTIVATE) && pip install --upgrade pip
    $(ACTIVATE) && pip install -r requirements.txt
    $(ACTIVATE) && playwright install

# ----------------------------------------
# Run the LinkedIn scraper
# ----------------------------------------
scrape:
    $(ACTIVATE) && $(PYTHON) scraper.py

# ----------------------------------------
# Lint (optional)
# ----------------------------------------
lint:
    $(ACTIVATE) && pylint scraper.py

# ----------------------------------------
# Format code (optional)
# ----------------------------------------
format:
    $(ACTIVATE) && black .

# ----------------------------------------
# Clean environment
# ----------------------------------------
clean:
    rm -rf $(VENV)
    find . -type d -name "__pycache__" -exec rm -rf {} +

# ----------------------------------------
# Full reset (clean + install)
# ----------------------------------------
reset: clean install
