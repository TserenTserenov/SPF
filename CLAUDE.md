# CLAUDE.md — SPF (Second Principles Framework)

> **Общие инструкции:** см. `/Users/tserentserenov/Github/CLAUDE.md`
>
> Этот файл содержит только специфику данного репозитория.

---

## 1. Тип репозитория

**Framework** — фреймворк вторых принципов (форма + процесс для Pack'ов).

**Source-of-truth:** Да (для спецификации SPF).

---

## 2. Что такое SPF

**SPF (Second Principles Framework)** задаёт:
- **Форму** — каноническая структура Pack'а
- **Процесс** — как создавать и эволюционировать Pack
- **Контракты** — связь source-of-truth с downstream

SPF **НЕ задаёт** предметное содержание — только форму и процесс.

---

## 3. Иерархия

```
FPF (Level 1)   →  First Principles Framework (мета-онтология)
       ↓                   ↑ upstream
SPF (Level 2)   →  ВЫ ЗДЕСЬ (форма + процесс)
       ↓                   ↓ downstream
Pack            →  spf-personal-pack, spf-ecosystem-pack, ...
```

---

## 4. Структура репозитория

```
SPF/
├── docs/               # Концептуальная документация
│   ├── conceptual-model.md
│   └── fpf-spf-pack.md   # Полная концептуальная модель
├── process/            # Процесс создания Pack
│   ├── 00-process-overview.md
│   ├── 01-domain-selection.md
│   ├── 02-bounded-context.md
│   ├── 03-distinctions-work.md
│   ├── ...
│   ├── process-lint.md
│   └── material-ingestion-protocol.md
├── spec/               # Спецификации
│   ├── ai-view.md
│   ├── downstream-contract.md
│   ├── human-guides.md
│   └── ids-and-references.md
└── pack-template/      # Шаблон структуры Pack
    ├── 00-pack-manifest.md
    ├── 01-domain-contract/
    ├── 02-domain-entities/
    ├── 03-methods/
    ├── 04-work-products/
    ├── 05-failure-modes/
    ├── 06-sota/
    └── 07-map/
```

---

## 5. Hard Bans (запреты)

### 5.1 Запрет дидактики
**ЗАПРЕЩЕНО в SPF и Pack:** "step", "lesson", "in N days", "implement", "first/then", "exercise", "module", "week 1"

**ПРИЧИНА:** Дидактика — downstream. Pack фиксирует **что существует**, а не **как учить**.

### 5.2 Запрет предметного содержания в SPF
**SPF задаёт форму**, не содержание. Содержание — в Pack'ах.

### 5.3 Запрет путаницы типов сущностей

| ❌ Путаница | ✅ Различение |
|------------|--------------|
| Method = Tool | Метод — способ действия, инструмент — средство |
| Method = Scenario | Метод — что, сценарий — пошагово как |
| Work Product = Description | WP — артефакт, description — нарратив |
| System = Episteme | Система — физическая сущность, эпистема — область знания |

---

## 6. Роль Claude в SPF

### 6.1. Что Claude ДЕЛАЕТ

| Роль | Описание |
|------|----------|
| **Spec Guardian** | Следит за соответствием спецификациям SPF |
| **Process Guide** | Помогает следовать процессу создания Pack |
| **Template Maintainer** | Поддерживает актуальность шаблонов |
| **Lint Runner** | Проверяет корректность изменений |

### 6.2. Что Claude НЕ ДЕЛАЕТ

- ~~Domain Expert~~ — не определяет что истинно в предметной области
- ~~Content Creator~~ — не генерирует знания из ничего
- ~~Downstream Builder~~ — курсы/код это другие репо

---

## 7. Ключевые документы

| Документ | Путь | Описание |
|----------|------|----------|
| Концептуальная модель (кратко) | `docs/conceptual-model.md` | FPF → SPF → Pack → Downstream |
| Концептуальная модель (полная) | `docs/fpf-spf-pack.md` | Детальное описание всей архитектуры |
| Process overview | `process/00-process-overview.md` | Обзор процесса |
| Process lint | `process/process-lint.md` | Правила проверки |
| Downstream contract | `spec/downstream-contract.md` | Контракт с downstream |
| Pack template | `pack-template/` | Каноническая структура Pack |

---

## 8. Процедуры

### 8.1 Изменение спецификации SPF

1. Определи, какой spec затронут (`spec/`, `process/`, `pack-template/`)
2. Проверь, не нарушит ли изменение существующие Pack'и
3. Обнови спецификацию
4. Обнови `process-lint.md` если нужно
5. Уведоми downstream (Pack репозитории)

### 8.2 Изменение pack-template

1. Изменения должны быть обратно-совместимы
2. Если breaking change — требуется миграция Pack'ов
3. Обнови `spec/ids-and-references.md` если затронуты ID

---

## 9. Pre-Commit Checklist

- [ ] Изменения не добавляют предметное содержание
- [ ] Изменения не добавляют дидактику
- [ ] Изменения обратно-совместимы (или задокументирован breaking change)
- [ ] `process-lint.md` обновлён если нужно
- [ ] Ссылки валидны

---

## 10. Связи с другими репозиториями

| Репозиторий | Связь |
|-------------|-------|
| ailev/FPF | Upstream — SPF следует FPF |
| spf-personal-pack | Downstream — Pack следует SPF |
| spf-ecosystem-pack | Downstream — Pack следует SPF |
| spf-digital-platform-pack | Downstream — Pack следует SPF |
