#!/usr/bin/env bash
# Verify the documentation's checkable claims against the repository.
# Exits non-zero if any check fails. Run from anywhere inside the repository.
#
# Note on style: every loop reads from a process substitution rather than a
# pipe, so that `fail=1` set inside it survives. A `while` on the right of a
# pipe runs in a subshell, and its exit status is discarded -- which would make
# this script print FAIL and still exit 0.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

fail=0
note() { printf '  %s\n' "$1"; }
bad() { printf '  FAIL: %s\n' "$1"; fail=1; }

echo "== 1. code citations in docs resolve =="
found=0
while IFS= read -r hit; do
  doc="${hit%%:*}"
  ref=$(printf '%s' "$hit" | grep -oE '(src|tests|experiments|examples)/[A-Za-z0-9_/]+\.py:[0-9][0-9,-]*' | head -1)
  [ -z "$ref" ] && continue
  found=$((found + 1))
  f="${ref%%:*}"; ln="${ref#*:}"; ln="${ln%%[,-]*}"
  if [ ! -f "$f" ]; then
    bad "$doc cites missing file $f"
  elif [ "$ln" -gt "$(wc -l <"$f")" ]; then
    bad "$doc cites $ref, beyond end of file"
  else
    printf '  %-44s -> %s\n' "$ref" "$(sed -n "${ln}p" "$f" | sed 's/^ *//' | cut -c1-60)"
  fi
done < <(grep -rn -oE '(src|tests|experiments|examples)/[A-Za-z0-9_/]+\.py:[0-9][0-9,-]*' --include='*.md' . 2>/dev/null)
note "$found citations checked - read the arrows: does each line say what the doc claims?"
note "citations under a 'describes the v1.0.0 code' banner are historical by design"

echo "== 2. every make target named in docs exists =="
while IFS= read -r t; do
  grep -q "^${t}:" Makefile || bad "docs reference undefined target: make $t"
done < <(grep -rhoE '`make [a-z][a-z-]*`' --include='*.md' . | tr -d '`' | sed 's/make //' | sort -u)
note "only backticked 'make x' is checked, so prose like 'make the' is ignored"

echo "== 3. markdown links resolve =="
while IFS= read -r pair; do
  f="${pair%%|*}"; l="${pair#*|}"
  p="${l%%#*}"; [ -z "$p" ] && continue
  [ -e "$p" ] || bad "$f links to missing $p"
done < <(for f in *.md; do
  [ -e "$f" ] || continue
  grep -o '\[[^]]*\]([^)]*)' "$f" | sed 's/.*(\(.*\))/\1/' | grep -v '^http' | sed "s|^|$f\||"
done)
note "relative links in top-level docs"

echo "== 4. tracked-file policy matches reality =="
if git ls-files | grep -q '\.png$'; then
  bad "PNGs are tracked, but the docs state that no figure is committed"
else
  note "no figures tracked, as documented"
fi
for csv in experiments/results/comparison_dense.csv experiments/results/comparison_sparse.csv; do
  git ls-files --error-unmatch "$csv" >/dev/null 2>&1 ||
    bad "$csv should stay tracked - it carries the evidence behind VERIFICATION.md"
done

echo "== 5. declared dependencies are reachable =="
for dep in numpy matplotlib pandas qiskit scipy seaborn; do
  grep -rqE "^[[:space:]]*(import|from) ${dep}\b" --include='*.py' . ||
    bad "$dep declared in pyproject.toml but never imported"
done
# Known indirect dependency: pandas.DataFrame.to_markdown() requires tabulate.
if grep -rq 'to_markdown' --include='*.py' . && ! grep -q '^tabulate' pyproject.toml; then
  bad "to_markdown() is used but tabulate is not declared - breaks at runtime, not at lint"
fi
note "after any dependency change run: pytest -k sparse   (lint cannot catch indirect use)"

echo
if [ "$fail" -eq 0 ]; then
  echo "audit: no failures (section 1 still needs your eyes)"
else
  echo "audit: FAILURES above"
fi
exit "$fail"
