# SPF — Second Principles Framework

> **Тип репозитория:** `Framework`

> Фреймворк для формализации вторых принципов предметных областей в инженерное знание.

## Что это

**SPF (Second Principles Framework)** — это фреймворк требований и процессов, который задаёт, **как вторые принципы** конкретной предметной области могут быть зафиксированы и стабилизированы как **инженерное знание**.

SPF отвечает на вопрос:
> Какая форма и какие критерии нужны, чтобы вторые принципы стали проверяемым ядром области?

## Ключевые понятия

| Термин | Определение |
|--------|-------------|
| **Вторые принципы** | Устойчивые предметные закономерности и различения внутри конкретной области |
| **Pack (паспорт области)** | Оформленное инженерное ядро области — результат применения SPF |
| **FPF** | First Principles Framework — мета-онтология и базовые различения, на которых основан SPF |

## Что SPF задаёт

**Минимальные обязательные элементы инженерного описания области:**
- Bounded context (границы области)
- Ключевые различения (distinctions)
- Характеристики и индикаторы
- Методы оценки/проверки
- Рабочие продукты
- Failure modes (типовые ошибки)
- SoTA-статусы и критерии пересмотра

**Требования к структуре:**
- Правила идентификаторов и ссылок
- Каноническая структура pack'а

**Процессные гейты:**
- Process lint: проверка корректности
- Контракты между source-of-truth и downstream

## Структура репозитория

```
SPF/
├── README.md              # Этот файл
├── REPO-TYPE.md           # Тип репозитория
├── docs/                  # Концептуальная документация
│   └── conceptual-model.md
├── process/               # Процесс создания pack
│   ├── 00-process-overview.md
│   ├── 01-domain-selection.md
│   ├── 02-bounded-context.md
│   ├── 03-distinctions-work.md
│   ├── 04-domain-entities-identification.md
│   ├── 05-information-ingestion.md
│   ├── 06-analysis-and-formalization.md
│   ├── 07-method-and-product-extraction.md
│   ├── 08-failure-modes-extraction.md
│   ├── 09-sota-annotation.md
│   ├── 10-map-maintenance.md
│   ├── 11-review-and-evolution-cycle.md
│   ├── material-ingestion-protocol.md
│   └── process-lint.md
├── spec/                  # Спецификации
│   ├── ai-view.md
│   ├── downstream-contract.md
│   ├── human-guides.md
│   └── ids-and-references.md
└── pack-template/         # Шаблон структуры pack
    ├── 00-pack-manifest.md
    ├── 01-domain-contract/
    ├── 02-domain-entities/
    ├── 03-methods/
    ├── 04-work-products/
    ├── 05-failure-modes/
    ├── 06-sota/
    └── 07-map/
```

## Что SPF НЕ делает

- **Не добавляет предметное содержание** — SPF не знает, какие вторые принципы верны в вашей области
- **Не строит курсы** — обучение это downstream
- **Не заменяет исследование/экспертизу** — SPF задаёт форму, не содержание

## Иерархия уровней

```
FPF (Level 1)  →  фреймворк первых принципов (мета-онтология + различения)
       ↓
SPF (Level 2)  →  фреймворк вторых принципов (форма + процесс)  ← ВЫ ЗДЕСЬ
       ↓
Pack           →  формализованное знание конкретной области
       ↓
Downstream     →  производные представления (курсы, AI-агенты, руководства)
```

## Универсальность SPF

SPF **универсален по форме и процессу**, но **не по содержанию**:
- Структура pack'а одинакова для любых областей
- Процесс создания знания одинаков
- Lint и гейты одинаковы
- Но наполнение pack'а всегда доменно-специфично

## Связанные репозитории

| Репозиторий | Тип | Роль |
|-------------|-----|------|
| [ailev/FPF](https://github.com/ailev/FPF) | Framework | First Principles Framework (upstream) |
| [spf-personal-pack](https://github.com/aisystant/spf-personal-pack) | Pack | Область созидателя |
| [spf-ecosystem-pack](https://github.com/TserenTserenov/spf-ecosystem-pack) | Pack | Область экосистемы |
| [spf-digital-platform-pack](https://github.com/TserenTserenov/spf-digital-platform-pack) | Pack | Область ИТ-платформы |

## Как начать создавать pack

1. Изучите [концептуальную модель](docs/conceptual-model.md)
2. Следуйте [процессу](process/README.md)
3. Используйте [шаблон pack](pack-template/)
4. Проверяйте [lint](process/process-lint.md)

---

*SPF — Second Principles Framework*
