PYINSTALLER_SOURCE=../pyinstaller
PYINSTALLER=$(PYINSTALLER_SOURCE)/pyinstaller.py
PYTHON:=$(shell which python3)
WINE_PYTHON:=$(shell which wine) python
WIN_PYTHON=python

SOURCES=$(wildcard src/*.py)
EXCLUDE_MODULES=
PYINSTALLER_FLAGS=-p src -F --windowed --onefile --workpath $(PYINSTALLER_CONFIG_DIR) --specpath $(PYINSTALLER_CONFIG_DIR) --exclude-module ipykernel

MAX_DIST_FILE_SIZE=100000

STATIC_TEST_GUI_TARGETS=demo_static_test_gui mk2_static_test_gui # These all depend on static_test_gui.py
TARGETS=$(STATIC_TEST_GUI_TARGETS) flight_gui
LIBS=Telemetry
STATIC_TEST_GUI_BIN_TARGETS=$(addprefix dist/, $(TARGETS))
STATIC_TEST_GUI_EXE_TARGETS=$(addsuffix .exe, $(STATIC_TEST_GUI_BIN_TARGETS))
BIN_TARGETS=$(addprefix dist/, $(TARGETS))
EXE_TARGETS=$(addsuffix .exe, $(BIN_TARGETS))
LIB_TARGETS=$(addsuffix .zip, $(addprefix libs/, $(LIBS)))
DRIVER_SOURCES=$(addsuffix .py, $(BIN_TARGETS))

# TODO: Figure out WSL build of linux binary on windows
ifeq ($(OS),Windows_NT)
  ALL_TARGETS=$(EXE_TARGETS) $(LIB_TARGETS)
else
  ALL_TARGETS=$(BIN_TARGETS) $(EXE_TARGETS) $(LIB_TARGETS)
endif

dist/%.exe: export PYINSTALLER_CONFIG_DIR = build/windows
dist/%:     export PYINSTALLER_CONFIG_DIR = build/linux

all: $(ALL_TARGETS)
bin: $(BIN_TARGETS)
exe: $(EXE_TARGETS)
lib: $(LIB_TARGETS)

# Raise an error if pyinstaller is missing
$(PYINSTALLER_SOURCE):
	$(error Error: $@ appears to be missing, did you clone https://github.com/pyinstaller/pyinstaller in the same directory?)

# All static test gui varients depend on static_test_gui.py
$(STATIC_TEST_GUI_BIN_TARGETS) $(STATIC_TEST_GUI_EXE_TARGETS): drivers/static_test_gui.py

dist/%.exe: drivers/%.py $(SOURCES) $(PYINSTALLER_SOURCE)
	@echo "Building $@"
	mkdir -p $(PYINSTALLER_CONFIG_DIR)
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$*/cycler*.egg 
ifeq ($(OS),Windows_NT)
# TODO: make sure this actually works on Windows
	$(WIN_PYTHON) $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
else
	$(WINE_PYTHON) $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
endif
	@if [ `du -k $@ | cut -f1` -ge $(MAX_DIST_FILE_SIZE) ]; then\
	  rm $@;\
	  echo "Error: $@ is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

dist/%: drivers/%.py $(SOURCES) $(PYINSTALLER_SOURCE)
	@echo "Building $@"
	mkdir -p $(PYINSTALLER_CONFIG_DIR)
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$*/cycler*.egg 
	$(PYTHON) $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $@ | cut -f1` -ge $(MAX_DIST_FILE_SIZE) ]; then\
	  rm $@;\
	  echo "Error: $@ is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

libs/%.zip: include/% include/%/* | libs
	@echo "Building $@"
	cd include && zip -r ../$@ $*

libs:
	mkdir -p libs

typecheck:
	mypy $(SOURCES) $(TARGET_SOURCES) --ignore-missing-imports

commit: all
	git add $(ALL_TARGETS)
	git commit -m "Updated dist files"

clean:
	rm -rf $(ALL_TARGETS) build/

clobber:
	rm -rf dist build libs

.PHONY: all bin exe lib setup typecheck commit clean
.NOTPARALLEL: # Unfourtunately now required by Pyinstaller
