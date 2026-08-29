.PHONY: all stl visuals scale-drawing design-docs package test clean

all: stl visuals scale-drawing design-docs

stl:
	python3 tools/generate_stl.py --output build

visuals: stl
	python3 tools/create_visuals.py --stl-dir build --output-dir output

scale-drawing:
	python3 tools/create_scale_drawing.py --output output/pdf/tang-nano-9k-panel-case-1to1.pdf

design-docs:
	python3 tools/create_retention_design.py --output output/pdf/tang-nano-9k-panel-case-retention-design.pdf

package: all
	python3 tools/package_artifacts.py --output-dir dist

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -f build/*.stl
	rm -rf output
	rm -rf dist
