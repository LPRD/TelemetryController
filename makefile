SOURCES=src/*.py

PYINSTALLER=build_tools/pyinstaller/pyinstaller.py
PY_VENV_ACTIVATE=build_tools/linux_venv/bin/activate
WINE_VENV_ACTIVATE=build_tools/wine_venv/bin/activate
NATIVE_WINE=0

EXCLUDE_MODULES=
PYINSTALLER_FLAGS=-p src -F --windowed --specpath build

MAX_SIZE=100000

TARGETS=flight_gui static_test_gui
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

# Raise an error if anything in build_tools is missing or modified
# These only get built when missing
$(PYINSTALLER) $(PY_VENV_ACTIVATE) $(WINE_VENV_ACTIVATE):
	$(error Error: $@ appears to be missing, did you clone with --recursive?  You can fix this with "git submodule update --recursive --init")

# TODO: make sure this can work on Windows
ifeq ($(OS),Windows_NT)
dist/%.exe: drivers/%.py $(SOURCES) $(PY_VENV_ACTIVATE) $(PYINSTALLER)
else
dist/%.exe: drivers/%.py $(SOURCES) $(WINE_VENV_ACTIVATE) $(PYINSTALLER)
endif
	@echo "Building $@"
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$*/cycler*.egg 
ifeq ($(OS),Windows_NT)
	. $(PY_VENV_ACTIVATE); python $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
else
	. $(WINE_VENV_ACTIVATE); wine python $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
endif
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

dist/%: drivers/%.py $(SOURCES) $(PY_VENV_ACTIVATE) $(PYINSTALLER)
	@echo "Building $@"
# Needed b/c pyinstaller sometimes chokes when this already exists
	rm -rf build/$*/cycler*.egg 
	. $(PY_VENV_ACTIVATE); python3 $(PYINSTALLER) $(PYINSTALLER_FLAGS) $<
	@if [ `du -k $< | cut -f1` -ge $(MAX_SIZE) ]; then\
	  rm $<;\
	  echo "Error: $< is larger than the github limit of 100 MB";\
	  exit 1;\
	fi

commit: all
	git add $(ALL_TARGETS)
	git commit -m "Updated dist files"

clean:
	rm -rf dist build

.PHONY: all bin exe setup commit clean
