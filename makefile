SOURCES=src/*.py

PYINSTALLER_PATH=build_tools/pyinstaller/pyinstaller.py
PY_VENV_ACTIVATE=build_tools/linux_venv/bin/activate

EXCLUDE_MODULES=
PYINSTALLER_FLAGS=-F --windowed --specpath build

MAX_SIZE=100000

TARGETS=flight_test_gui static_test_gui
BIN_TARGETS=$(addprefix dist/, $(TARGETS))
EXE_TARGETS=$(addsuffix .exe, $(BIN_TARGETS))

ifeq ($(OS),Windows_NT)
  ALL_TARGETS=$(EXE_TARGETS)
else
  WINE_CHECK:=$(shell wine python -c 'import matplotlib; import serial' 2>/dev/null; echo $$?)
  ifeq (0,$(WINE_CHECK))
    ALL_TARGETS=$(BIN_TARGETS) $(EXE_TARGETS)
  else
    $(warning wine does not appear to be set up correctly, exe build is disabled)
    ALL_TARGETS=$(BIN_TARGETS)
  endif
endif

all: $(ALL_TARGETS)
bin: $(BIN_TARGETS)
exe: $(EXE_TARGETS)

setup:
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$target/cycler*.egg 
	@echo "Building $(ALL_TARGETS)"

dist/%.exe: src/%.py setup $(SOURCES)
ifeq ($(OS),Windows_NT)
	python $(PYINSTALLER_PATH) $(PYINSTALLER_FLAGS) $<
else
	wine python $(PYINSTALLER_PATH) $(PYINSTALLER_FLAGS) $<
endif
	@if [ `du -k $@ | cut -f1` -ge $(MAX_SIZE) ]; then echo "Error: $@ is larger than the github limit of 100 MB"; rm $@; exit 1; fi

dist/%: src/%.py setup $(SOURCES)
	. $(PY_VENV_ACTIVATE); python3 $(PYINSTALLER_PATH) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $@ | cut -f1` -ge $(MAX_SIZE) ]; then echo "Error: $@ is larger than the github limit of 100 MB"; rm $@; exit 1; fi

commit: all
	git add dist --ignore-removal
	git commit -m "Updated dist files"

clean:
	rm -rf dist build

.PHONY: all bin exe setup clean
