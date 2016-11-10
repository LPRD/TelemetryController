NATIVE_WINE=0
NATIVE_PYTHON=0

SOURCES=src/*.py
PYINSTALLER_SOURCE=build_tools/pyinstaller
WINE_VENV=build_tools/wine_venv
LINUX_VENV=build_tools/linux_venv

PYINSTALLER=$(PYINSTALLER_SOURCE)/pyinstaller.py
ifeq ($(NATIVE_WINE), 0)
WINE=$(WINE_VENV)/bin/wine
else
WINE:=$(shell which wine)
endif
ifeq ($(NATIVE_PYTHON), 0)
PYTHON=$(LINUX_VENV)/bin/python3
else
PYTHON:=$(shell which python3)
endif

EXCLUDE_MODULES=
PYINSTALLER_FLAGS=-p src -F --windowed --specpath build

MAX_SIZE=100000

TARGETS=flight_gui static_test_gui pressure_test_gui
LIBS=Telemetry
BIN_TARGETS=$(addprefix dist/, $(TARGETS))
EXE_TARGETS=$(addsuffix .exe, $(BIN_TARGETS))
LIB_TARGETS=$(addsuffix .zip, $(addprefix libs/, $(LIBS)))

# TODO: Figure out WSL build of linux binary on windows
ifeq ($(OS),Windows_NT)
  ALL_TARGETS=$(EXE_TARGETS) $(LIB_TARGETS)
else
  ALL_TARGETS=$(BIN_TARGETS) $(EXE_TARGETS) $(LIB_TARGETS)
endif

all: $(ALL_TARGETS)
bin: $(BIN_TARGETS)
exe: $(EXE_TARGETS)
lib: $(LIB_TARGETS)

# Raise an error if anything in build_tools is missing or modified
# These only get built when missing
$(PYINSTALLER_SOURCE) $(LINUX_VENV) $(WINE_VENV):
	$(error Error: $@ appears to be missing, did you clone with --recursive?  You can fix this with "git submodule update --recursive --init")

# TODO: make this actually works on Windows
ifeq ($(OS),Windows_NT)
dist/%.exe: drivers/%.py $(SOURCES) $(PYINSTALLER_SOURCE) | $(PY_VENV)
else
dist/%.exe: drivers/%.py $(SOURCES) $(PYINSTALLER_SOURCE) | $(WINE_VENV)
endif
	@echo "Building $@"
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$*/cycler*.egg 
ifeq ($(OS),Windows_NT)
	python $(PYINSTALLER) $(PYINSTALLER_FLAGS) $< # TODO: Use a virtualenv on windows
else
	$(WINE) python $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
endif
	@if [ `du -k $@ | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $@;\
	  echo "Error: $@ is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

dist/%: drivers/%.py $(SOURCES) $(PYINSTALLER_SOURCE) | $(PY_VENV)
	@echo "Building $@"
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$*/cycler*.egg 
	$(PYTHON) $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $@ | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $@;\
	  echo "Error: $@ is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

libs/%.zip: include/% include/%/* | libs
	@echo "Building $@"
	cd include && zip -r ../$@ $*

libs:
	mkdir -p libs

commit: all
	git add $(ALL_TARGETS)
	git commit -m "Updated dist files"

clean:
	rm -rf dist build libs

.PHONY: all bin exe lib setup commit clean
