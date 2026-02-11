---
id: SPF.SPEC.003
name: Масштабируемость Pack
status: draft
created: 2026-02-11
---

# Масштабируемость Pack

> Спецификация SPF: как строить Pack, который остаётся понятным для ИИ-агентов при росте на порядки.

---

## Проблема

Pack загружается в контекстное окно ИИ-агента целиком. При текущем объёме (~30 файлов, ~5K строк) это работает. При росте (100+ файлов, 15K+ строк) — перестаёт: контекст переполняется, LLM теряет точность на длинном контексте (lost-in-the-middle effect), стоимость растёт линейно.

**Порог:** ~100 файлов / ~15K строк — граница context-loading подхода.

---

## Различение: Context-loading ≠ Retrieval-based

| Режим | Описание | Когда работает | Предел |
|-------|----------|----------------|--------|
| **Context-loading** | Весь Pack загружается в контекст | <100 файлов, <15K строк | ~200K токенов |
| **Retrieval-based** | Агент запрашивает нужные части через поиск | Любой объём | Качество retrieval |

**Стратегия:** подготовить Pack к retrieval-based загрузке, не ломая context-loading для малых Pack.

---

## SOTA-методы (обоснование решений)

### Что применимо к Pack

| Метод | Источник | Применение в Pack |
|-------|----------|-------------------|
| **RAPTOR** (Hierarchical Indexing) | Stanford, 2024 | Pack уже имеет 3 уровня: manifest → MAP → entity cards. Формализовать как layers |
| **Contextual Chunking** | Anthropic, 2024 | Добавить `summary` в frontmatter каждой entity — retrieval без чтения всего файла |
| **Hybrid Retrieval** (dense + BM25) | Production default 2025 | Vector search по summary + точный поиск по ID-кодам |
| **LightRAG** | HKUDS, EMNLP 2025 | Typed `related:` в frontmatter формируют граф — traversal по связям |
| **MemGPT/Letta** | UCB, 2023 | 3-слойная память: core (manifest) + recall (MAP/indices) + archival (entity cards) |
| **llms.txt** | llmstxt.org, 2024 | Manifest как machine-readable index всех entities |
| **Context Engineering** | Anthropic, 2025 | Write/Select/Compress/Isolate — Pack поддерживает все 4 стратегии через layers |

### Что НЕ применимо

| Метод | Почему не подходит |
|-------|--------------------|
| Подпапки по типу сущности | Решает проблему человека, не ИИ. ИИ навигирует по индексам, не по папкам |
| Статические `_index.md` | Устаревают так же, как ручной MAP. Нужна генерация |
| Full GraphRAG (Microsoft) | Избыточен для структурированного Pack. LightRAG-style через frontmatter `related:` достаточен |

---

## Спецификация: 3-слойная загрузка

### Принцип

ИИ-агент загружает Pack послойно: от обзора к деталям. Каждый слой самодостаточен для своего уровня задач.

### Layer 0: Always-in-context (≤2K токенов)

Загружается всегда, при любом обращении к Pack.

| Файл | Содержание | Макс. размер |
|------|------------|-------------|
| `00-pack-manifest.md` | ID, scope, entity count, version, entity index с summary | 1.5K токенов |
| `01A-bounded-context.md` | Объект описания, scope, truth criteria (summary) | 500 токенов |

**Требование:** manifest ДОЛЖЕН содержать machine-readable таблицу ВСЕХ entities с 1-строчным summary (см. § Расширенный Manifest).

### Layer 1: On-demand indices (≤5K токенов каждый)

Загружается при навигации, поиске связей, планировании работы.

| Файл | Содержание | Когда загружать |
|------|------------|-----------------|
| `07-map/DOMAIN.MAP.001.md` | Полная навигация (автогенерируемая) | Нужен обзор всех связей |
| `01B-distinctions.md` | Все различения с summary | Работа с концепциями |
| `02C-methods-index.md` | Все методы с inputs/outputs | Работа с методами |

### Layer 2: Full entity cards (≤1K токенов каждая)

Загружается точечно, по ID.

| Файл | Когда загружать |
|------|-----------------|
| `DOMAIN.M.NNN-*.md` | Нужны детали метода |
| `DOMAIN.WP.NNN-*.md` | Нужны критерии продукта |
| `DOMAIN.FM.NNN-*.md` | Анализ ошибок |

**Протокол загрузки:**

```
1. Агент получает задачу
2. Загружает Layer 0 (manifest + bounded context)
3. По manifest находит нужные entities (по summary и tags)
4. Загружает Layer 1 index для навигации (если нужно)
5. Загружает конкретные entity cards из Layer 2
```

---

## Расширенный Manifest

Manifest ДОЛЖЕН содержать секцию **Entity Index** — полный перечень всех сущностей с summary:

```markdown
## Entity Index

| ID | Name | Kind | Summary | Status |
|----|------|------|---------|--------|
| DP.D.001 | Объект ≠ Модель | D | Модель упрощает; нельзя путать абстракцию с реальностью | active |
| DP.M.001 | Извлечение знаний | M | Трансформация сырой информации в pack-совместимые сущности | active |
| DP.WP.001 | Extraction Report | WP | Структурированный отчёт экстракции с классификациями | active |
| DP.FM.001 | Информация как знание | FM | Необработанная информация принимается за формализованное знание | active |
```

**Требование:** Entity Index генерируется автоматически из frontmatter файлов (см. § Auto-MAP).

---

## Расширенный Frontmatter

### Новые обязательные поля

```yaml
---
id: DOMAIN.M.XXX
name: Method Name
status: draft | active | deprecated
summary: "One sentence describing this entity for retrieval and index generation"
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---
```

**`summary`** (обязательное, новое):
- Одно предложение, ≤150 символов
- Достаточное для понимания сущности без чтения полного файла
- Используется в Entity Index, MAP, и retrieval

### Новые опциональные поля

```yaml
---
# ... обязательные поля ...
related:
  produces: [DOMAIN.WP.001]        # Typed: что производит
  uses: [DOMAIN.D.006, DOMAIN.D.001]  # Typed: что использует
  fails_with: [DOMAIN.FM.001]      # Typed: какие ошибки
  requires_role: [DOMAIN.R.001]    # Typed: какие роли нужны
  precedes: [DOMAIN.M.002]         # Typed: что предшествует
  follows: [DOMAIN.M.003]          # Typed: что следует
  component_of: [DOMAIN.M.004]     # Typed: часть чего
tags: [extraction, knowledge, formalization]  # Для поиска
---
```

**`related` (типизированный):**
- Заменяет плоский список `related: [DP.WP.001, DP.FM.002]`
- Каждая связь имеет тип (produces, uses, fails_with, etc.)
- Позволяет строить Knowledge Graph и навигировать по связям
- Обратная совместимость: плоский список по-прежнему валиден, но deprecated

**`tags`:**
- Свободные метки для полнотекстового поиска
- Дополняют ID-based навигацию семантическим поиском

---

## Auto-MAP

### Требование

MAP (`07-map/DOMAIN.MAP.001.md`) ДОЛЖЕН генерироваться автоматически из frontmatter файлов Pack.

### Механизм

1. Скрипт `scripts/generate-map.py` (шаблон в SPF)
2. Запуск: вручную, pre-commit hook, или CI
3. Входные данные: все `.md` файлы Pack с YAML frontmatter
4. Выходные данные: обновлённый MAP + Entity Index в manifest

### Что генерируется

- Таблицы: Core Distinctions, Methods, Work Products, Failure Modes, SoTA Annotations
- Граф зависимостей (из typed `related:`)
- Статистика: counts, coverage, staleness (entities not updated >90 days)
- Предупреждения: broken links, missing summary, unregistered kinds

---

## Sub-Pack Protocol

### Когда выделять Sub-Pack

Pack выделяет под-домен в отдельный Pack когда:

1. **Появляется отдельный bounded context** — с собственным объектом описания и truth criteria
2. **Файлов >100** в одном поддомене (индикатор, не критерий)
3. **Появляется отдельный maintainer** — другой человек/команда ведёт эту часть знаний

**Тест:** если можно написать самостоятельный bounded context (01A) для поддомена — это Sub-Pack.

### Механизм

1. Создать новый Pack-репо с отдельным `pack_id`
2. Зарегистрировать в реестре контекстов (SPF.SPEC.001)
3. Установить cross-pack ссылки
4. Оригинальный Pack ссылается на Sub-Pack в manifest (Dependencies)

---

## Будущее: MCP-сервер для Pack

> Это описание архитектуры, не требование текущей версии.

При объёме Pack >100 файлов рекомендуется MCP-сервер с tools:

| Tool | Описание |
|------|----------|
| `pack_search(query, kind?)` | Поиск entities по summary/tags + optional фильтр по виду |
| `pack_get(id)` | Загрузка полной entity card по ID |
| `pack_list(kind)` | Список всех entities определённого вида |
| `pack_graph(id, depth?)` | Граф связей entity (из typed related) |
| `pack_stats()` | Статистика Pack: counts, staleness, coverage |

Реализация: Python + frontmatter parser + vector search (embeddings summary полей).

---

## Чеклист для авторов Pack

- [ ] Каждая entity card имеет `summary` в frontmatter
- [ ] `related:` типизирован (produces, uses, fails_with, etc.)
- [ ] Entity Index в manifest актуален (или auto-generated)
- [ ] MAP генерируется автоматически (скрипт настроен)
- [ ] При >50 файлов: проверить — нет ли кандидатов на Sub-Pack
- [ ] При >100 файлов: рассмотреть MCP-сервер для retrieval

---

## Обратная совместимость

| Изменение | Совместимость |
|-----------|---------------|
| `summary` в frontmatter | Новое обязательное поле. Существующие Pack: добавить при следующем обновлении |
| Typed `related:` | Плоский список по-прежнему валиден, но deprecated. Мигрировать постепенно |
| `tags` | Опциональное. Без обратной несовместимости |
| Auto-MAP | Ручной MAP по-прежнему валиден. Авто-генерация — рекомендация, не требование |
| Entity Index в manifest | Новая обязательная секция. Добавить при следующем обновлении |

---

*Этот документ: `SPF.SPEC.003`*
