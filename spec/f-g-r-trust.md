# F-G-R Trust Pattern (Optional)

> **FPF Reference:** B.3 (Trust & Assurance Calculus)
> Полная спецификация: `~/Github/FPF/FPF-Spec.md`

## Overview

F-G-R — это паттерн из FPF для оценки **доверительности** (trust) утверждений. Он может использоваться в Pack'ах для более строгой оценки качества знания.

**Статус:** Опциональный паттерн. Большинство Pack'ов могут работать без него. Рекомендуется для:
- Pack'ов в критических областях (безопасность, медицина)
- Ситуаций, когда нужно явно показать уровень уверенности
- Работы с гипотезами и недоказанными утверждениями

---

## F-G-R Tuple

Trust — это не "ощущение", а вычисляемый кортеж `⟨F, G, R⟩`:

| Компонент | Название | Вопрос | Значения |
|-----------|----------|--------|----------|
| **F** | Formality | Насколько строго это выражено? | F0 (sketch) → F9 (formal proof) |
| **G** | Claim Scope | Где это применимо? | Set-valued (контексты, где утверждение верно) |
| **R** | Reliability | Насколько это подтверждено? | Evidence-based support level |

---

## F: Formality Scale

| Level | Description | Example |
|-------|-------------|---------|
| F0 | Sketch, informal | "I think X works" |
| F1-F2 | Written but loose | Blog post, notes |
| F3-F4 | Structured text | Method card with definition |
| F5-F6 | Checked specification | Reviewed by expert |
| F7-F8 | Tested/validated | Has tests, passed review |
| F9 | Formal proof | Mathematical/logical proof |

---

## G: Claim Scope

G определяет **где** утверждение верно. Это set-valued (множество контекстов).

| Scope | Example |
|-------|---------|
| Universal | "Method ≠ Tool" (верно везде в FPF-aligned systems) |
| Domain-wide | "Агентность — ключевая характеристика" (верно в Pack созидателя) |
| Context-specific | "Метод X работает для Y" (верно в конкретных условиях) |

---

## R: Reliability

R показывает **насколько хорошо** утверждение поддержано доказательствами.

| Level | Evidence | Example |
|-------|----------|---------|
| Low | Hypothesis, no test | "Мы думаем, что..." |
| Medium | Some evidence | "Практика показывает..." |
| High | Strong evidence | "Исследования подтверждают..." |
| Very High | Replicated | "Многократно проверено" |

---

## When to Use F-G-R in Pack

### Recommended

| Situation | Why |
|-----------|-----|
| Critical distinctions | Show that core distinctions are well-established |
| Controversial claims | Be explicit about confidence level |
| Hypotheses | Make clear these need validation |
| Cross-references | Show alignment quality with FPF |

### Not Required

| Situation | Why |
|-----------|-----|
| Simple method cards | SoTA status is sufficient |
| Obvious distinctions | Standard format covers them |
| Work products | They are artifacts, not claims |

---

## Integration with SoTA

F-G-R дополняет SoTA:

| SoTA | F-G-R |
|------|-------|
| Status (current/hypothesis/deprecated) | Детальная оценка (F, G, R) |
| Revision criterion | Что изменит F, G, или R |
| Simple | More detailed |

Можно использовать SoTA без F-G-R, но F-G-R без SoTA — нет смысла.

---

## Example Annotation

```markdown
**Claim:** Method and Tool are distinct types (D.001)

**F-G-R:**
- **F** = 6 (Checked specification, reviewed)
- **G** = {SPF, Pack, all FPF-aligned systems}
- **R** = High (consistent with FPF A.7, no counter-evidence)

**SoTA:** `current`
- Revision criterion: Would change if evidence shows tool can substitute method
```

---

## References

- FPF B.3: Trust & Assurance Calculus
- FPF B.3.1: Components & Epistemic Spaces
- FPF B.3.3: Assurance Subtypes & Levels
- FPF B.3.4: Evidence Decay & Epistemic Debt
