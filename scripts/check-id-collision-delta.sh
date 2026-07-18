#!/usr/bin/env bash
# check-id-collision-delta.sh — delta-aware ID-collision guard for Pack repos.
# see DP.SC.181, WP-388 Ф14 (ArchGate 2026-06-14, вариант A).
#
# Два независимых чека:
#  1. ID-коллизия: staged-added entity-файл вносит ID (PREFIX.TYPE.N), уже
#     занятый другим файлом/секцией в репо.
#  2. Режим различений: staged-правка *-distinctions.md добавляет НОВУЮ секцию
#     поверх порога масштабируемости (2026-07-18, реконсиляция SPF.SPEC.003 ↔
#     process/03-distinctions-work.md — драйв дрейфа DP.D.249/250).
# Невинные правки и уникальные новые ID проходят. Дополняет глобальный
# pack-lint (warning) и CI check-pack-collisions.sh (бэкстоп).
#
# Корень проблемы 1: параллельные агенты в одной рабочей папке независимо
# берут max+1 и сталкиваются (WP-388 Ф14). find сканирует рабочее дерево,
# поэтому ловит и незакоммиченный файл второго агента до push.
#
# Корень проблемы 2: после того как *-distinctions.md пересекает порог
# масштабируемости, новые различения обязаны идти отдельным файлом
# (02-domain-entities/<DOMAIN>.D.<NNN>-slug.md), не новой секцией — иначе
# воссоздаётся тот же двойной реестр, что дал коллизию DP.D.249/250. Ниже
# порога файл ещё в single-file режиме — рост секциями легитимен. Правки/
# переименования/удаление существующих секций (число секций не растёт)
# разрешены в обоих режимах.
#
# Exit codes:
#   0 — коллизий/нарушений режима нет (или нечего проверять)
#   1 — один из чеков нашёл нарушение (коммит блокируется)

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
[ -z "$REPO_ROOT" ] && exit 0

ID_RE='^[A-Z]+\.[A-Z]+\.[0-9]+'
status=0

# Все entity-файлы репо с их ID (исключая .git/archive/inbox/template).
# Печатает строки "ID<TAB>path". Точное сравнение ID, без glob-границ (180 ≠ 1800).
# 2026-07-18 (дрейф DP.D): скан секционных ID внутри multi-entity файлов
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

# --- Чек 1: ID-коллизия (staged-added .md под pack/, delta-aware) ---
ADDED=$(git diff --cached --name-only --diff-filter=A -- 'pack/*.md' 'pack/**/*.md' 2>/dev/null || true)

if [ -n "$ADDED" ]; then
  ENTITY_INDEX=$(all_entity_ids)

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
    echo "   → переименуй новый файл на следующий свободный ID (имя файла + поле id: внутри)."
    echo ""
  done <<< "$ADDED"
fi

# --- Чек 2: режим различений (staged-added/modified *-distinctions.md) ---
DIST_MODE_THRESHOLD=40  # см. SPF.SPEC.003 § Size limit + process/03-distinctions-work.md § Output
D_HEADER_RE='^#{2,3} +\[?[A-Z]+\.D\.[0-9]+\]?'
DIST_CHANGED=$(git diff --cached --name-only --diff-filter=ACM -- 'pack/*.md' 'pack/**/*.md' 2>/dev/null \
  | grep -E -- '-distinctions\.md$' \
  | grep -Ev '/(\.git|archive|inbox)/' \
  | grep -Ev '/_[^/]*/' || true)

if [ -n "$DIST_CHANGED" ]; then
  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    git cat-file -e "HEAD:$rel" 2>/dev/null || continue  # новый файл (новый/маленький Pack, режим ещё не выбран) — пропуск

    head_n=$(git show "HEAD:$rel" 2>/dev/null | grep -cE "$D_HEADER_RE" || true)
    staged_n=$(git show ":$rel" 2>/dev/null | grep -cE "$D_HEADER_RE" || true)
    head_n=${head_n:-0}
    staged_n=${staged_n:-0}

    if [ "$head_n" -ge "$DIST_MODE_THRESHOLD" ] && [ "$staged_n" -gt "$head_n" ]; then
      status=1
      echo "🚫 Новая секция в $rel: было $head_n различений, стало $staged_n (порог single-file режима — $DIST_MODE_THRESHOLD)."
      echo "   Файл уже в режиме «индекс+карточка» (SPF.SPEC.003) — новое различение создавай"
      echo "   отдельным файлом <DOMAIN>.D.<NNN>-slug.md в 02-domain-entities/, не новой секцией здесь."
      echo ""
    fi
  done <<< "$DIST_CHANGED"
fi

[ "$status" -eq 0 ] && exit 0

echo "Это блок гарда ID-коллизий/режима различений (WP-388 Ф14, SPF.SPEC.003), а не сбой. Обойти нельзя — исправь по подсказке выше."
exit 1
