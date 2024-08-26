.PHONY: help test cov format run clean check hard_check hard_check_full docs

help:					## Show this help
	@printf "Usage : make <target> \n\nThe following targets are available:\n\n"
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n"

test:	## Run unit tests
	sudo apt-get install fonts-ipafont-gothic ghostscript libjpeg8-dev libfreetype6-dev
	pip install -U docutils tox
	# Run tox
	tox -- -v

format:	## Reformat all Python files
	black *.py test/*.py plugins/*.py

clean:	## Remove all generated files
	-rm -rf _build
	-rm -rf .tox
	-rm -rf __pycache__ src/nwdiag/__pycache__ src/packetdiag/__pycache__ src/rackdiag/__pycache__
	-rm -rf .venv
	-rm -rf .venv310
	-rm requirements_dev.txt
	-rm -rf docs/build
	-rm -rf docs/source/README.md
	-rm -rf dist
	-rm -rf src/nwdiag_nocher.egg-info

SHELL := /bin/bash

env:	## Create and activate a local virtual dev env
	sudo apt update
	sudo apt install -y python3 python3.10-venv
	python3.10 -m venv .venv310
	source .venv310/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pip install -e .

VERSION := $(shell nwdiag --version)

build:	## Generate distribuable archives
	#python -m hatch build
	sudo python3 setup.py install

run: env
	source .venv310/bin/activate && python src/run.py examples/nwdiag/simple.diag

docker-build: build		## Build full sized Docker image
	docker build -t "nwdiag:latest" -f Dockerfile .

docker-build-slim:		## Build Docker image with optimal size
	docker build -t "nwdiag-slim:latest" -f Dockerfile_slim .

docker-run:	docker-build			## Run a fresh, clean Python container
	docker run --rm \
	 -v ${PWD}/examples/nwdiag:/app \
	 -t "nwdiag:latest" \
	 nwdiag simple_with_custom_trunk_diameter.diag; \
	ls -al examples/nwdiag/

docker-run-slim:	docker-build-slim			## Run a fresh, clean Python container
	docker run --rm \
	 -v ${PWD}/examples/nwdiag:/app \
	 -t "nwdiag-slim:latest" \
	 nwdiag simple_with_custom_trunk_diameter.diag; \
	ls -al examples/nwdiag/