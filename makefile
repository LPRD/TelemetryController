SOURCES=src/*.py

PYINSTALLER=build_tools/pyinstaller/pyinstaller.py
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

all: setup $(ALL_TARGETS)
bin: setup $(BIN_TARGETS)
exe: setup $(EXE_TARGETS)

setup: build_tools
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/*/cycler*.egg 
	@echo "Building $(ALL_TARGETS)"

# These only get built when missing
$(PYINSTALLER) $(PY_VENV_ACTIVATE) $(WINE_VENV_ACTIVATE):
	$(error Error: $@ appears to be missing, did you clone with --recursive?  You can fix this with "git submodule update --recursive --init")

ifeq ($(OS),Windows_NT)
dist/%.exe: src/%.py setup $(SOURCES) $(PY_VENV_ACTIVATE) $(PYINSTALLER)
	. $(PY_VENV_ACTIVATE); python $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi
else
dist/%.exe: src/%.py setup $(SOURCES) $(PY_VENV_ACTIVATE) $(PYINSTALLER)
	. $(WINE_VENV_ACTIVATE); wine python $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi
endif

dist/%: src/%.py setup $(SOURCES) $(PY_VENV_ACTIVATE) $(PYINSTALLER)
	. $(PY_VENV_ACTIVATE); python3 $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
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
