#!/usr/bin/env bash
# check-id-collision-delta.sh — delta-aware ID-collision guard for Pack repos.
# see DP.SC.181, WP-388 Ф14 (ArchGate 2026-06-14, вариант A).
#
# Блокирует коммит ТОЛЬКО когда staged-added entity-файл вносит ID
# (PREFIX.TYPE.N), уже занятый другим файлом в репо. Невинные правки и
# уникальные новые ID проходят. Дополняет глобальный pack-lint (warning) и
# CI check-pack-collisions.sh (бэкстоп).
#
# Корень проблемы: параллельные агенты в одной рабочей папке независимо берут
# max+1 и сталкиваются (WP-388 Ф14). find сканирует рабочее дерево, поэтому
# ловит и незакоммиченный файл второго агента до push.
#
# Exit codes:
#   0 — коллизий нет (или нечего проверять)
#   1 — добавляемый файл занимает существующий ID (коммит блокируется)

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
[ -z "$REPO_ROOT" ] && exit 0

# staged-added .md под pack/ (только новые файлы — delta-aware)
ADDED=$(git diff --cached --name-only --diff-filter=A -- 'pack/*.md' 'pack/**/*.md' 2>/dev/null || true)
[ -z "$ADDED" ] && exit 0

ID_RE='^[A-Z]+\.[A-Z]+\.[0-9]+'

# Все entity-файлы репо с их ID (исключая .git/archive/inbox/template).
# Печатает строки "ID<TAB>path". Точное сравнение ID, без glob-границ (180 ≠ 1800).
# 2026-07-18 (дрейф DP.D): добавлен скан секционных ID внутри multi-entity файлов
# («### DP.D.NNN:», «## [DP.D.NNN]») — 01B-distinctions.md несёт ~130 секций,
# basename-скан был к ним слеп → коллизии файлов с секциями (DP.D.034/249/250 и др.).
all_entity_ids() {
  {
    find "$REPO_ROOT" -name '*.md' -type f 2>/dev/null \
      | grep -Ev '/(\.git|archive|inbox)/' \
      | grep -Ev '/_[^/]*/' \
      | while IFS= read -r path; do
          eid=$(basename "$path" | grep -oE "$ID_RE" || true)
          [ -n "$eid" ] && printf '%s\t%s\n' "$eid" "$path"
        done
    grep -rHoE '^#{2,3} +\[?[A-Z]+\.[A-Z]+\.[0-9]+\]?' "$REPO_ROOT/pack" --include='*.md' 2>/dev/null \
      | grep -Ev '/(\.git|archive|inbox)/' \
      | grep -Ev '/_[^/]*/' \
      | sed -E 's/^(.*\.md):#{2,3} +\[?([A-Z]+\.[A-Z]+\.[0-9]+)\]?.*$/\2\t\1/' \
      || true
  } | sort -u
}

ENTITY_INDEX=$(all_entity_ids)
status=0

while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  id=$(basename "$rel" | grep -oE "$ID_RE" || true)
  [ -z "$id" ] && continue   # не ID-несущий файл (например, 00-pack-manifest.md)

  abs="$REPO_ROOT/$rel"
  others=$(printf '%s\n' "$ENTITY_INDEX" \
    | awk -F'\t' -v id="$id" '$1==id{print $2}' \
    | grep -vF "$abs" || true)

  [ -z "$others" ] && continue

  status=1
  prefix=$(printf '%s' "$id" | grep -oE '^[A-Z]+\.[A-Z]+')
  maxn=$(printf '%s\n' "$ENTITY_INDEX" \
    | awk -F'\t' -v p="$prefix." 'index($1, p)==1{print $1}' \
    | grep -oE '[0-9]+$' | sort -n | tail -1)
  nextn=$(( ${maxn:-0} + 1 ))

  echo "🚫 ID-коллизия: добавляемый файл занимает уже существующий $id"
  echo "   добавляемый: $rel"
  printf '%s\n' "$others" | sed "s|^$REPO_ROOT/|   конфликт:   |"
  echo "   следующий свободный: $prefix.$nextn"
  echo ""
done <<< "$ADDED"

[ "$status" -eq 0 ] && exit 0

echo "Переименуй новый файл на следующий свободный ID (имя файла + поле id: внутри)."
echo "Это блок гарда ID-коллизий (WP-388 Ф14), а не сбой. Обойти нельзя — разведи номер."
exit 1
