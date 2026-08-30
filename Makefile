.PHONY: all check env-check stl visuals scale-drawing design-docs package test container-build container-check clean

CONTAINER_ENGINE ?= podman
CONTAINER_IMAGE ?= tang-nano-9k-case-dev

all: stl visuals scale-drawing design-docs

check: env-check test package

env-check:
	scripts/check-env.sh

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

container-build:
	$(CONTAINER_ENGINE) build -f Containerfile -t $(CONTAINER_IMAGE) .

container-check: container-build
	$(CONTAINER_ENGINE) run --rm --network none -v "$(CURDIR):/project" -w /project $(CONTAINER_IMAGE) make check

clean:
	rm -f build/*.stl
	rm -rf output
	rm -rf dist
