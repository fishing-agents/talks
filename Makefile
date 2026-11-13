DECKS := snow_corp_cncf kcd_vietnam coscup_2026 ossummit_korea hitcon_lightning hami_cross_platform_observability ossummit_europe_agents gpu_workshop kubecon_na_contribfest kubecon_na_contribfest_booth
HTMLS := $(addprefix dist/,$(addsuffix .html,$(DECKS)))
PDFS  := $(HTMLS:.html=.pdf)
TAG   ?= v$(shell date +%Y.%m.%d)
DECKTILE_SPEC := decktile[plot]>=0.3.4
DECKTILE_PY = $(shell uv tool dir)/decktile/bin/python

all: $(HTMLS)

pdf: $(PDFS)

release: pdf
	gh release create $(TAG) $(PDFS) assets/demo/llm_test.mp4 --generate-notes

# Installs or upgrades decktile with the seaborn extra when it is missing or too old.
check:
	@command -v uv >/dev/null || { echo "uv not found: https://docs.astral.sh/uv/"; exit 1; }
	@$(DECKTILE_PY) -c "import seaborn, importlib.metadata as m, sys; v = tuple(map(int, m.version('decktile').split('.')[:3])); sys.exit(v < (0, 3, 4))" 2>/dev/null \
		|| uv tool install --upgrade '$(DECKTILE_SPEC)'

dist/%.html: %.deck.md | check
	decktile $<

dist/%.pdf: %.deck.md | check
	decktile --pdf $<

watch-%: %.deck.md | check
	decktile -w $<

clean:
	rm -rf dist/

.PHONY: all pdf release check clean watch-%
