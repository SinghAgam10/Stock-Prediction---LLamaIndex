
# Variables
VENV_PATH = venv
PYTHON = $(VENV_PATH)/bin/python3.10
venv_creation=python3 -m venv venv
PIP = $(VENV_PATH)/bin/pip3.10

activate_venv = . $(VENV_PATH)/bin/activate &&

.PHONY: install
install:
install:
	$(venv_creation)
	$(activate_venv) $(PIP) install firebase-admin "grpcio <= 1.40.0" && $(PIP) install -r requirements.txt

.PHONY: makevenv
makevenv:
makevenv:
	$(venv_creation)
	$(activate_venv) pip install --upgrade pip
	$(DONE)

.PHONY: run
run:
run:
	$(activate_venv) $(PYTHON) $(file)

.PHONY: install-run
install-run:
install-run:
	$(activate_venv) $(PIP) install -r requirements.txt
	$(PYTHON) app.py

.PHONY: clean
clean:
clean:
	rm -rf $(VENV_PATH)