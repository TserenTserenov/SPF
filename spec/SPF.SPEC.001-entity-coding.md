---
id: SPF.SPEC.001
name: Entity Coding Rule
status: draft
created: 2026-02-10
---

# Entity Coding Rule

> SPF specification: how to identify and code entities across all Packs and in SPF itself.

---

## Foundation (FPF)

### Object ≠ Description ≠ Carrier

FPF (A.7 Strict Distinction) requires distinguishing:

| Level | What it is | Example |
|-------|-----------|---------|
| **Object** | Thing in reality | Knowledge extraction method (capability) |
| **Description** | Episteme about the thing (U.Episteme) | Method card in Pack |
| **Carrier** | Physical/digital medium (U.SymbolCarrier) | File `DP.M.001-knowledge-extraction.md` |

**Pack contains descriptions of domain entities on carriers (`.md` files).** The code indicates what is being described, not the level of description.

---

## Terminology

### Entity types

SPF defines **base types** — they may appear in any domain.

| Type | EN | Definition | not (what this is NOT) |
|------|----|-----------|-----------------------|
| **Method** | Method | Description of a capability to produce a work product | not a scenario (step-by-step instruction), not a tool, not execution (work) |
| **Work Product** | Work Product | Observable result of applying a method; exists on a carrier | not a method description, not a skill |
| **Failure Mode** | Failure Mode | Typical violation of a method or work product with observable symptoms | not a code bug, not a risk (probability) |
| **Distinction** | Distinction | Conceptual boundary whose violation creates irresolvable confusion | not a fact, not a definition |
| **Role** | Role | Contextual function (mask) in a bounded context | not a position, not a person, not behavior |
| **Characteristic** | Characteristic | Measurable evaluation axis for an entity | not a metric (measurement), not an indicator (observable sign) |
| **SoTA Annotation** | SoTA Annotation | Currency status of a statement + revision criterion | not a literature review |
| **Map** | Map | Navigation structure of connections between entities | = structural artifact, not content |

### Domain entities

A Pack may contain entities specific to its bounded context. For these, the Pack defines **extended types** and registers them in the manifest (`00-pack-manifest.md`).

### Distinction: type ≠ characteristic

- **Type** — category of the entity (what it belongs to): method, role, work product.
- **Characteristic** — measurable axis (how the entity is evaluated): complexity, maturity, currency.

Type answers "what is it?". Characteristic answers "what is it like?".

---

## Coding rule

### Code format

All identifiable entities are coded by a single rule:

```
<CONTEXT>.<TYPE>.<NUMBER>
```

| Segment | Format | Definition |
|---------|--------|-----------|
| CONTEXT | 2–4 uppercase Latin letters | Bounded context mnemonic (FPF: U.BoundedContext) — semantic frame with its own vocabulary, roles and invariants |
| TYPE | 1–6 uppercase Latin letters | Entity type code. Base types — from SPF; extended types — from Pack |
| NUMBER | 3 digits | Sequential numbering within context + type |

### Code properties

1. **Immutability** — code does not change after assignment
2. **Uniqueness** — one code = one entity, forever
3. **No reuse** — deleted/deprecated entities retain their code
4. **Sequence** — numbers are assigned in order of creation
5. **Gaps are permitted** — `001, 002, 005` is valid (003, 004 may be deprecated)

---

## Type codes

### Base types (defined by SPF, available to all Packs)

| Code | Type | Folder in Pack |
|------|------|---------------|
| `M` | Method | `03-methods/` |
| `WP` | Work Product | `04-work-products/` |
| `FM` | Failure Mode | `05-failure-modes/` |
| `D` | Distinction | `01-domain-contract/` |
| `R` | Role | `02-domain-entities/` |
| `CHR` | Characteristic | `02-domain-entities/` |
| `SOTA` | SoTA Annotation | `06-sota/` |
| `MAP` | Map | `07-map/` |
| `SC` | Service Clause | `08-service-clauses/` |

### Extended types (defined by a specific Pack)

A Pack may define additional types for its domain entities. They:

- Are registered in the Pack manifest (`00-pack-manifest.md`)
- Are placed in `02-domain-entities/`
- Code: 1–6 uppercase Latin letters, unique within the Pack

### SPF types (for the framework itself)

| Code | Type | Description |
|------|------|-------------|
| `SPEC` | Specification | Normative specification (rule) |
| `TPL` | Template | Structure template |
| `D` | Distinction | Distinction (common to all Packs) |
| `MAP` | Map | SPF navigation map |

---

## Levels and coding

| Level | Codes itself? | Format | Creates new codes? |
|-------|--------------|--------|--------------------|
| **FPF** | Yes | `U.*` (own format) | Yes (meta-level) |
| **SPF** | Yes | `SPF.TYPE.NUMBER` | Yes (form rules) |
| **Pack** | Yes | `CONTEXT.TYPE.NUMBER` | Yes (domain knowledge) |
| **Downstream** | No | References Pack codes | No |

---

## Context registry

| Code | Context | Level | Repo |
|------|---------|-------|------|
| `SPF` | Second Principles Framework | Framework | SPF/ |
| `PD` | Personal Development | Pack | PACK-personal/ |
| `DP` | Digital Platform | Pack | PACK-digital-platform/ |
| `EC` | Ecosystem | Pack | PACK-ecosystem/ |
| `MIM` | Engineering Managers Workshop | Pack | PACK-MIM/ |
| `VR` | Verification & Acceptance | Pack | PACK-verification/ |

Requirements for a new context code:

- 2–4 uppercase Latin letters
- Bounded context mnemonic
- Globally unique (in this registry)

---

## File name

```
<CODE>-<slug>.md
```

- **Code** — full entity code
- **Slug** — Latin characters, kebab-case, without repeating the number

Examples:

```
SPF.SPEC.001-entity-coding.md
DP.M.001-knowledge-extraction.md
DP.AISYS.013-knowledge-extractor.md
EC.R.001-mentor.md
```

---

## References

### Within a single Pack

```markdown
See [DP.M.001](../03-methods/DP.M.001-knowledge-extraction.md)
```

### Cross-Pack references

```markdown
See [DP.M.001](https://github.com/.../03-methods/DP.M.001-knowledge-extraction.md)
```

With version:

```markdown
See [DP.M.001@v1.0.0](https://github.com/...@v1.0.0/.../DP.M.001-knowledge-extraction.md)
```

### References to FPF

```markdown
Per FPF, method ≠ tool (see FPF A.7, Strict Distinction).
```

### In YAML Frontmatter

```yaml
---
id: DP.M.001
name: Knowledge Extraction
status: active
created: 2026-02-10
related:
  - DP.WP.001
  - DP.FM.002
---
```

---

## Validation

Codes are validated for:

- [ ] Format: `CONTEXT.TYPE.NNN`
- [ ] Uniqueness within repo
- [ ] File exists at expected path
- [ ] All references resolve
- [ ] Extended types are registered in Pack manifest

---

*This document: `SPF.SPEC.001`*
