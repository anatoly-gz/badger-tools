.PHONY: export-all clean

export-all: $(patsubst src/%.py,pages/%.html,$(wildcard src/*.py))

pages/%.html: src/%.py
	mkdir -p pages
	uvx marimo export html-wasm "$<" --no-sandbox --mode run --single-file -o "$@"

clean:
	rm -rf pages
