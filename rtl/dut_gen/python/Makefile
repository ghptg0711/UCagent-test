CURRENT_DIR := $(shell pwd)
NPROC := $(shell (nproc 2>/dev/null || sysctl -n hw.ncpu) 2>/dev/null)
.PHONY: all test compile clean purge copy_xspcomm

all: test clean
	@echo "All complete"

test: compile
	@rm *.a 2>/dev/null || true
	@echo "--------------Compile Success Test Step DUT--------------------"
	@cd ../ && PYTHONPATH=.:/usr/local/share/picker/python/xspcomm/.. python3 example.py && rm -rf *.fst *.vcd *.fsdb *.log *.key 2>/dev/null || (echo "Error: Test failed, plz check whether behavior is correct" && sleep 10)
	@echo "--------------------------------------------------------------"

# copy xspcomm lib
copy_xspcomm_lib=true
ifneq ($(copy_xspcomm_lib), true)
copy_xspcomm:
	@echo "Ignore copy python module: xspcomm"
else
copy_xspcomm:
	@echo "Try copy python module: xspcomm"
	@cp -r /usr/local/share/picker/python/xspcomm xspcomm
endif

compile: copy_xspcomm
	@echo "start build wrapper at" && date
	cmake . -Bbuild
	cmake --build build --config Debug --parallel $(NPROC)
	@cp build/_${TARGET}.so .
	@cp build/lib${TARGET}.py .
	@touch ../__init__.py
	@echo "end build wrapper at" && date

clean:
	@rm -rf *.fst *.vcd *.fsdb *.log *.key build

purge: clean
	@rm -rf *.txt Makefile *.hpp *.cmake *.i __pycache__
	@rm ../__init__.py || true
	@find . -mindepth 1 -maxdepth 1 -not -name '*.vdb' -exec mv -t ../ {} + 2>/dev/null || true
	@echo "purge complete"
	@rm -rf $(CURRENT_DIR)
