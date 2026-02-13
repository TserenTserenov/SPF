---
id: SPF.DOC.SOTA-MAPPING
name: SPF ↔ SOTA Mapping
status: draft
created: 2026-02-13
---

# SPF ↔ SOTA Mapping

> Таблица соответствий: SPF-слоты и SOTA-практики, которые их заполняют.
> Source: Pack DP `06-sota/DP.SOTA.*` + SPF.SPEC.003

## Позиционирование

| Уровень | Что | Роль |
|---------|-----|------|
| FPF | Метапринципы корректного мышления | Первые принципы |
| SPF | Спецификация ядра предметной области | Вторые принципы |
| SOTA | Лучшие методы из индустрии | Заполнители слотов SPF |
| DDD | Метод добычи и инженерной реализации ядра | Операционализация SPF |

> SPF определяет СЛОТЫ. SOTA заполняет слоты МЕТОДАМИ. DDD — мост между ними.

## Маппинг: SPF-слот → SOTA-практика

| SPF-слот | SOTA-практика | ID | Что даёт |
|----------|---------------|----|----------|
| Bounded Context | DDD Strategic | DP.SOTA.001 | Context Mapping, ACL, Published Language |
| Словарь (Kinds, термины) | DDD (Ubiquitous Language) | DP.SOTA.001 | UL прорастает везде: код, UI, docs, тикеты |
| Инварианты / вторые принципы | DSL→DSLM | DP.SOTA.010 | Machine-checkable domain rules |
| Boundary Statements | Open API Specs | DP.SOTA.003 | OpenAPI + AsyncAPI + CloudEvents |
| Multi-View представления | Multi-Representation Arch | DP.SOTA.012 | viewOf, compositionViewOf, projectionView |
| Проекция в Downstream | Multi-Representation Arch | DP.SOTA.012 | Pack → multiple views |
| Интеграция контекстов | Coupling Model | DP.SOTA.011 | knowledge/distance/volatility coupling |
| Evidence / Assurance | DDD + Open Specs | DP.SOTA.001/003 | Domain tests + contract testing |
| Эволюция модели | DDD Strategic | DP.SOTA.001 | Refactoring toward deeper insight |
| Разделение политики и механизма | Context Engineering | DP.SOTA.002 | Write/Select/Compress/Isolate |

## Маппинг: SPF Layer → SOTA-метод (Pack Architecture)

| SPF Layer | SOTA-метод | Что делает |
|-----------|-----------|-----------|
| Layer 0 (manifest) | llms.txt, MemGPT/Letta (core) | Machine-readable index, always-in-context |
| Layer 0 (summary) | Contextual Chunking | Retrieval без чтения полного файла |
| Layer 1 (MAP, indices) | RAPTOR, MemGPT/Letta (recall) | Hierarchical navigation |
| Layer 2 (entity cards) | MemGPT/Letta (archival) | Точечная загрузка по ID |
| Cross-entity links | LightRAG | Typed `related:` = граф для traversal |
| Semantic search | Hybrid Retrieval | Vector (summary) + exact (ID-codes) |

## Маппинг: Операционный цикл → SOTA-практика

| Операция | SOTA-практика | ID | Как применяется |
|----------|---------------|----|-----------------|
| Создание Pack | DDD Strategic | DP.SOTA.001 | BC identification, UL extraction |
| Экстракция знаний | AI-Accelerated OE | DP.SOTA.007 | LLM first pass, human validates |
| Capture (during work) | Real-Time KM | DP.SOTA.008 | На рубежах, не после сессии |
| Проектирование агента | Agentic Development | DP.SOTA.006 | BC + IPO + контракты |
| Контекст агента | Context Engineering | DP.SOTA.002 | Write/Select/Compress/Isolate |
| Организация агентов | AI-Native Org | DP.SOTA.005 | Each agent = org unit with accountability |
| Оценка связей | Coupling Model | DP.SOTA.011 | 3 измерения: knowledge/distance/volatility |
| Retrieval | GraphRAG | DP.SOTA.004 | Vector + graph traversal |
| Digital Twin | KB Digital Twins | DP.SOTA.009 | Pack + данные + агенты |

## Что НЕ применимо (с обоснованием)

| Практика | Почему не SOTA / не применимо |
|----------|-------------------------------|
| Тактический DDD (Entity, VO, Aggregate) | ООП-специфика, не универсальна за пределами Java/C# (DP.D.017) |
| Формальные domain specifications (академические) | Не мейнстрим; заменены онтологиями + KG |
| Full GraphRAG (Microsoft) | Избыточен для структурированного Pack; LightRAG достаточен |
| Статические `_index.md` | Устаревают; заменены auto-MAP |
| Подпапки по типу сущности | Решает проблему человека, не ИИ |

---

*Edition: 2026-02 | Обновлять при изменении SOTA-практик в Pack DP*
