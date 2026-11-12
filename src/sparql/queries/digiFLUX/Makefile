ENDPOINT  := https://lindas.admin.ch/query
FORMATS   := xml json csv tsv
DEFAULT   := json
QUERIES   := $(sort $(wildcard queries/*.rq))
NAMEWIDTH := 40

ACCEPT_xml  := application/sparql-results+xml
ACCEPT_json := application/sparql-results+json
ACCEPT_csv  := text/csv
ACCEPT_tsv  := text/tab-separated-values

ROWS_FN = rows() { case "$$1" in \
  csv)     python3 -I -c 'import csv,sys; print(sum(1 for _ in csv.reader(open(sys.argv[1], newline=""))) - 1)' "$$2" 2>/dev/null || echo $$(( $$(wc -l < "$$2") - 1 )) ;; \
  tsv)     echo $$(( $$(wc -l < "$$2") - 1 )) ;; \
  xml)     grep -o '<result>' "$$2" | wc -l ;; \
  json)    python3 -I -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["results"]["bindings"]))' "$$2" 2>/dev/null || echo '?' ;; \
  esac; }

.PHONY: all clean help FORCE $(FORMATS)

all: $(DEFAULT)

help:
	@sed -n '2,10p' $(MAKEFILE_LIST) | sed 's/^# \{0,1\}//'

clean:
	rm -rf data

FORCE:

$(foreach f,$(FORMATS),$(eval $(f): $(patsubst queries/%.rq,data/$(f)/%.$(f),$(QUERIES))))
$(FORMATS):
	@$(ROWS_FN); \
	total=$$(for f in data/$@/*.$@; do rows $@ "$$f"; done | awk '{s+=$$1} END {print s}'); \
	printf '\nDone. %s tables, %s rows in total, saved to data/%s/\n' "$$(ls data/$@/*.$@ | wc -l)" "$$total" "$@"

fmt  = $(patsubst .%,%,$(suffix $@))
name = $(notdir $(basename $@))

.SECONDEXPANSION:
data/%: queries/$$(notdir $$(basename $$*)).rq FORCE
	@mkdir -p $(@D)
	@n='$(name)'; if [ $${#n} -gt $(NAMEWIDTH) ]; then n="$$(printf '%.$(shell expr $(NAMEWIDTH) - 3)s' "$$n")..."; fi; printf '%-$(NAMEWIDTH)s ' "$$n"
	@$(ROWS_FN); \
	if curl --silent --show-error --fail -X POST "$(ENDPOINT)" \
	      -H "Content-Type: application/sparql-query" \
	      -H "Accept: $(ACCEPT_$(fmt))" \
	      --data-binary "@$<" -o "$@"; then \
	  printf '%7s rows %9s bytes\n' "$$(rows $(fmt) "$@")" "$$(wc -c < "$@")"; \
	else \
	  echo "FAILED"; rm -f "$@"; exit 1; \
	fi
