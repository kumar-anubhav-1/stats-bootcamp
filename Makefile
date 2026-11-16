all:        ## full build: data, tests, anomaly register, recipe checks, site
	./build.sh
quick:      ## skip data regeneration and tests
	./build.sh --quick
serve:      ## quick build, then serve the site locally
	./build.sh --quick --serve
data:       ## regenerate the teaching data only
	python -m datagen.generate
instructor: ## instructor-only: truth pack, held-out exam and transfer data, answer keys
	python -m datagen.generate --domain all --with-truth --exam --transfer
	python -m tools.instructor_pack
.PHONY: all quick serve data instructor
