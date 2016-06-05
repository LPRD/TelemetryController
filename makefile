SOURCES=src/*.py

PYINSTALLER_PATH=build_tools/pyinstaller/pyinstaller.py
PY_VENV_ACTIVATE=build_tools/linux_venv/bin/activate
WINE_VENV_ACTIVATE=build_tools/wine_venv/bin/activate
NATIVE_WINE=0

EXCLUDE_MODULES=
PYINSTALLER_FLAGS=-F --windowed --specpath build

MAX_SIZE=100000

TARGETS=flight_test_gui static_test_gui
BIN_TARGETS=$(addprefix dist/, $(TARGETS))
EXE_TARGETS=$(addsuffix .exe, $(BIN_TARGETS))

ifeq ($(OS),Windows_NT)
  ALL_TARGETS=$(EXE_TARGETS)
else
  ALL_TARGETS=$(BIN_TARGETS) $(EXE_TARGETS)
endif

all: $(ALL_TARGETS)
bin: $(BIN_TARGETS)
exe: $(EXE_TARGETS)

setup:
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/*/cycler*.egg 
	@echo "Building $(ALL_TARGETS)"

.init_wine:
ifneq ($(shell . $(WINE_VENV_ACTIVATE); wine python -c 'import matplotlib; import serial; import pywintypes' 2>/dev/null; echo $?), 0)
	@echo ". $(WINE_VENV_ACTIVATE)" > $@;
	@echo "Building with virtual WINE env";
else ifneq ($(shell wine python -c 'import matplotlib; import serial; import pywintypes' 2>/dev/null; echo $?), 0)
	@echo ":" > $@;
	@echo "Building with native WINE env";
else
	@echo "Error: build_tools appears to be missing, did you clone with --recursive?  You can fix this with git submodule update --recursive --init"
	@exit 1
endif

.init_python:
ifneq ($(shell . $(PY_VENV_ACTIVATE); python3 -c 'import matplotlib; import serial; import pywintypes' 2>/dev/null; echo $?), 0)
	@echo ". $(PY_VENV_ACTIVATE)" > $@
	@echo "Building with virtual python env"
else ifneq ($(shell python3 -c 'import matplotlib; import serial; import pywintypes' 2>/dev/null; echo $?), 0)
	@echo ":" > $@;
	@echo "Building with native python env";
else
	@echo "Error: build_tools appears to be missing, did you clone with --recursive?  You can fix this with git submodule update --recursive --init"
	@exit 1
endif

ifeq ($(OS),Windows_NT)
dist/%.exe: src/%.py setup $(SOURCES) .init_python $(PYINSTALLER_PATH)
	`cat .init_python`; python $(PYINSTALLER_PATH) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi
else
dist/%.exe: src/%.py setup $(SOURCES) .init_wine $(PYINSTALLER_PATH)
	`cat .init_wine`; wine python $(PYINSTALLER_PATH) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi
endif

dist/%: src/%.py setup $(SOURCES) .init_python $(PYINSTALLER_PATH)
	`cat .init_python`; python3 $(PYINSTALLER_PATH) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

commit: all
	git add dist --ignore-removal
	git commit -m "Updated dist files"

clean:
	rm -rf dist build .init_*

.PHONY: all bin exe setup commit clean
