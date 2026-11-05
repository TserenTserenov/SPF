#!/usr/bin/env python3
"""
Auto-MAP Generator for SPF Packs.

Reads YAML frontmatter from all .md files in a Pack directory, plus ID-headed
sections of `*distinctions.md` files, and generates:
1. The navigation MAP file (07-map/<DOMAIN>.MAP.001.md or --map-id)
2. The Entity Index section of 00-pack-manifest.md (--manifest / --index-only)

Usage:
    python generate-map.py <pack-directory>
    python generate-map.py <pack-directory> --manifest      # map + manifest index
    python generate-map.py <pack-directory> --index-only    # manifest index only, no map
    python generate-map.py <pack-directory> --manifest --map-id VR.MAP.002
    python generate-map.py <pack-directory> --manifest --allow-drop ECO.D.014,ECO.D.015

Exit codes:
    0  success
    1  bad input (not a directory)
    2  map target conflict: the ID belongs to a hand-written map, two map files
       share the ID, or a map file has unparsable frontmatter. Nothing is written.
    3  Entity Index guard: IDs of the previous index would disappear (and are not
       exactly the --allow-drop list), or a previous index body could not be
       parsed. Nothing is written.

Scope of the index (deliberately narrower than check-id-collision-delta.sh,
which guards uniqueness over every ID-headed heading in pack/):
- every file with frontmatter `id`;
- every `##`/`###` section headed by an ID in a `*distinctions.md` file
  (the legacy distinctions registry; new distinctions are files, SPF.SPEC.003).
Other ID headings (catalog items inside an entity, section-level references to
existing files) are not pack entities; they are listed under
"Notes on indexed ID scope" inside the index so they stay visible.

Requirements:
    pip install pyyaml
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import yaml

# Base type codes from SPF.SPEC.001 "### Base types" table. Kept frozen here on
# purpose (no runtime read of the spec); test-generate-map.py checks the two agree.
BASE_KINDS = ("M", "WP", "FM", "D", "R", "CHR", "SOTA", "MAP", "SC")

# Three or more parts: DP.M.001, ECO.MAP.BIND.001.
ID_PATTERN = r"[A-Z]+(?:\.[A-Z]+)+\.[0-9]+"
# Heading shape of check-id-collision-delta.sh, with a capture group so
# "## [ECO.D.035]" yields "ECO.D.035".
SECTION_HEADING_RE = re.compile(
    r"^#{2,3} +\[?(" + ID_PATTERN + r")\]?(.*)$", re.MULTILINE
)
INDEX_HEADING_RE = re.compile(r"^##[ \t]+Entity Index\b[^\r\n]*", re.MULTILINE)
# Looser shape ("##Entity Index", "##  entity index") that the strict one misses.
LOOSE_INDEX_HEADING_RE = re.compile(
    r"^##\s*Entity\s+Index\b", re.MULTILINE | re.IGNORECASE
)
SECTION_END_RE = re.compile(r"^#{1,2}[ \t]", re.MULTILINE)
INSERT_ANCHOR_RE = re.compile(r"^## (Upstream|Changelog|Maintainers)\b", re.MULTILINE)
TRAILING_RULE_RE = re.compile(r"\r?\n---[ \t]*\r?\n\s*\Z")
INDEX_ROW_ID_RE = re.compile(r"^\|\s*(" + ID_PATTERN + r")\s*\|", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

SKIP_NAMES = ("00-pack-manifest.md", "ontology.md")
MAP_SUMMARY = "Auto-generated navigation map of all pack entities"

KIND_LABELS = {
    "D": "Distinctions",
    "R": "Roles",
    "M": "Methods",
    "WP": "Work Products",
    "FM": "Failure Modes",
    "SOTA": "SoTA Annotations",
    "MAP": "Maps",
    "CHR": "Characteristics",
    "SC": "Service Clauses",
    "OA": "Objects of Attention",
}


class GeneratorError(Exception):
    """A refusal with a defined exit code; raised before anything is written."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def read_frontmatter(filepath: Path) -> tuple[str, dict | None, str]:
    """Return (state, data, content); state is 'none', 'invalid' or 'ok'."""
    content = filepath.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return "none", None, content
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return "invalid", None, content
    if not isinstance(data, dict):
        return "invalid", None, content
    return "ok", data, content


def entity_from_frontmatter(
    filepath: Path, state: str, data, content: str
) -> dict | None:
    """Entity dict of a file whose frontmatter has `id`, or None."""
    if state != "ok" or data.get("id") in (None, ""):
        return None
    data["id"] = str(data["id"])
    data["_filepath"] = str(filepath)
    if "name" not in data:
        heading_match = re.search(r"^##\s+\[.*?\]\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            data["name"] = heading_match.group(1).strip()
        else:
            slug = re.sub(r"^[A-Z]+\.[A-Z]+\.\d+-?", "", filepath.stem)
            if slug:
                data["name"] = slug.replace("-", " ").title()
    return data


def parse_frontmatter(filepath: Path) -> dict | None:
    """Frontmatter of an entity file (one with `id`), or None."""
    try:
        state, data, content = read_frontmatter(filepath)
    except (OSError, UnicodeDecodeError) as err:
        print(f"Warning: unreadable file {filepath}: {err}", file=sys.stderr)
        return None
    return entity_from_frontmatter(filepath, state, data, content)


def classify_kind(entity_id: str) -> str:
    """Kind code of an ID: DP.M.001 -> M; legacy KIND.DOMAIN form D.ECO.001 -> D."""
    parts = entity_id.split(".")
    if len(parts) < 3:
        return "UNKNOWN"
    if parts[0] in BASE_KINDS and parts[1] not in BASE_KINDS:
        return parts[0]
    return parts[1]


def iter_pack_files(pack_dir: Path):
    for md_file in sorted(pack_dir.rglob("*.md")):
        if md_file.name.startswith("_") or md_file.name in SKIP_NAMES:
            continue
        yield md_file


def _is_map_file(md_file: Path, pack_dir: Path) -> bool:
    return "07-map" in md_file.relative_to(pack_dir).parts


def _section_name(rest: str) -> str:
    return rest.strip().lstrip(":—–-").strip() or "—"


def collect_entities(pack_dir: Path):
    """Return (entities, notes, id_warnings, quality_warnings).

    entities: file entities and distinctions sections, each a dict with id,
    name, summary, status and _source ('file' | 'section').
    notes: (class, id, relpath) for ID headings that are not indexed.
    id_warnings: ID-space problems (collisions, swapped pairs, unreadable
    files); shown in the index and the map. quality_warnings: missing fields;
    shown in the map only.
    """
    files = []
    sections = []
    other_headings = []
    unreadable = []
    for md_file in iter_pack_files(pack_dir):
        rel = str(md_file.relative_to(pack_dir))
        try:
            state, data, content = read_frontmatter(md_file)
        except (OSError, UnicodeDecodeError) as err:
            unreadable.append(f"Unreadable file: {rel} ({err})")
            continue
        fm = entity_from_frontmatter(md_file, state, data, content)
        if fm:
            fm["_source"] = "file"
            files.append(fm)
        generated = state == "ok" and bool(data.get("generated"))
        if _is_map_file(md_file, pack_dir) or generated:
            continue
        own_id = fm["id"] if fm else None
        for match in SECTION_HEADING_RE.finditer(content):
            sid, rest = match.group(1), match.group(2)
            if sid == own_id:
                continue
            if md_file.name.endswith("distinctions.md"):
                sections.append(
                    {
                        "id": sid,
                        "name": _section_name(rest),
                        "summary": f"Раздел в {rel}",
                        "status": "—",
                        "_source": "section",
                        "_rel": rel,
                    }
                )
            else:
                other_headings.append((sid, rel))

    file_ids = {e["id"] for e in files}
    entities = files + sections
    warnings = list(unreadable)
    quality_warnings = []
    for e in files:
        if "summary" not in e:
            quality_warnings.append(
                f"Missing `summary`: {e['id']} ({Path(e['_filepath']).name})"
            )
    origins = defaultdict(list)
    for e in entities:
        origins[e["id"]].append(
            e.get("_rel") or str(Path(e["_filepath"]).relative_to(pack_dir))
        )
    for eid, places in sorted(origins.items()):
        if len(places) > 1:
            warnings.append(
                f"Exact ID collision: {eid} appears {len(places)} times: {', '.join(places)}"
                " — pack owner: renumber all but one (SPF.SPEC.001)"
            )
    all_ids = file_ids | {s["id"] for s in sections}
    for eid in sorted(all_ids):
        parts = eid.split(".")
        if len(parts) != 3:  # e.g. ECO.MAP.BIND.001 has no swapped form
            continue
        a, b, n = parts
        swapped = f"{b}.{a}.{n}"
        if a in BASE_KINDS and b not in BASE_KINDS and swapped in all_ids:
            warnings.append(
                f"Swapped-format ID pair: {eid} and {swapped} are different entities"
                f" — pack owner: {eid} uses the legacy KIND.DOMAIN form (SPF.SPEC.001)"
            )

    notes = []
    for sid, rel in other_headings:
        cls = (
            "heading of an already indexed file"
            if sid in file_ids
            else "not a pack entity; pack owner: if it is a distinction of its own,"
            " move it to its own file (SPF.SPEC.003)"
        )
        notes.append((cls, sid, rel))
    return entities, notes, warnings, quality_warnings


def _cell(value) -> str:
    """Render a frontmatter value as one markdown table cell.

    Folded YAML scalars (`summary: >`) end with a newline and may span lines;
    written as-is they break the table row. Collapse whitespace and escape pipes.
    """
    return " ".join(str(value).split()).replace("|", "\\|")


def _sort_key(e):
    return (e["id"], e["_source"] != "file")


def _row(e, with_kind: bool) -> str:
    name = _cell(e.get("name", "—"))
    summary = _cell(e.get("summary", "—"))
    status = e.get("status", "—")
    if with_kind:
        return (
            f"| {e['id']} | {name} | {classify_kind(e['id'])} | {summary} | {status} |"
        )
    return f"| {e['id']} | {name} | {summary} | {status} |"


def generate_map(entities, warnings, map_id: str, created: str) -> str:
    """Generate MAP content. Group headings carry no IDs (no new collisions)."""
    by_kind = defaultdict(list)
    for e in entities:
        by_kind[classify_kind(e["id"])].append(e)

    today = date.today().isoformat()
    lines = [
        "---",
        f"id: {map_id}",
        "name: Pack Navigation Map",
        f"summary: {MAP_SUMMARY}",
        "scope: full-pack",
        f"created: {created}",
        f"last_updated: {today}",
        "generated: true",
        "---",
        "",
        f"# [{map_id}] Pack Navigation Map",
        "",
        f"> Auto-generated from frontmatter on {today}. Do not edit manually.",
        "",
        "---",
        "",
        "## Statistics",
        "",
        "| Kind | Count |",
        "|------|-------|",
    ]
    for kind in sorted(by_kind.keys()):
        label = KIND_LABELS.get(kind, kind)
        lines.append(f"| {label} ({kind}) | {len(by_kind[kind])} |")
    lines.append(f"| **Total** | **{len(entities)}** |")
    lines.append("")

    main_kinds = ["D", "R", "M", "WP", "FM", "SOTA", "MAP"]
    for kind in main_kinds:
        if kind not in by_kind:
            continue
        lines.append(f"## {KIND_LABELS.get(kind, kind)}")
        lines.append("")
        lines.append("| ID | Name | Summary | Status |")
        lines.append("|----|------|---------|--------|")
        lines.extend(_row(e, False) for e in sorted(by_kind[kind], key=_sort_key))
        lines.append("")

    extended = {k: v for k, v in by_kind.items() if k not in main_kinds + ["CHR", "OA"]}
    if extended:
        lines.append("## Domain-Specific Entities")
        lines.append("")
        for kind in sorted(extended.keys()):
            lines.append(f"### {KIND_LABELS.get(kind, kind)}")
            lines.append("")
            lines.append("| ID | Name | Summary | Status |")
            lines.append("|----|------|---------|--------|")
            lines.extend(_row(e, False) for e in sorted(extended[kind], key=_sort_key))
            lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {w}" for w in warnings)
        lines.append("")

    stale = []
    for e in entities:
        last_updated = e.get("last_updated")
        if isinstance(last_updated, str):
            try:
                last_updated = datetime.strptime(last_updated, "%Y-%m-%d").date()
            except ValueError:
                continue
        if isinstance(last_updated, date):
            days = (date.today() - last_updated).days
            if days > 90:
                stale.append((e["id"], days))
    if stale:
        lines.append("## Staleness Warnings (>90 days since update)")
        lines.append("")
        lines.append("| ID | Days Since Update |")
        lines.append("|----|-------------------|")
        lines.extend(
            f"| {eid} | {days} |" for eid, days in sorted(stale, key=lambda x: -x[1])
        )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by `scripts/generate-map.py` on {today}*")
    return "\n".join(lines)


def generate_entity_index(
    entities, notes, warnings, heading: str = "## Entity Index"
) -> str:
    """Entity Index section body; warnings and notes live inside it (### level)."""
    lines = [
        heading,
        "",
        "| ID | Name | Kind | Summary | Status |",
        "|----|------|------|---------|--------|",
    ]
    lines.extend(_row(e, True) for e in sorted(entities, key=_sort_key))
    if warnings:
        lines += ["", "### Warnings", ""]
        lines.extend(f"- {w}" for w in warnings)
    if notes:
        lines += [
            "",
            "### Notes on indexed ID scope",
            "",
            (
                "Only files with frontmatter `id` and ID-headed sections of"
                " `*distinctions.md` are indexed. These ID headings are not:"
            ),
            "",
        ]
        lines.extend(f"- {sid} in {rel} — {cls}" for cls, sid, rel in notes)
    return "\n".join(lines)


def find_index_spans(content: str) -> list[tuple[int, int, str]]:
    """(start, end, heading_line) of every Entity Index section.

    A section ends at the next h1/h2 heading or EOF. A heading that only the
    loose pattern recognises ("##Entity Index") is refused: replacing around it
    would leave its IDs unguarded and add a second index.
    """
    strict = {m.start() for m in INDEX_HEADING_RE.finditer(content)}
    loose = [m.start() for m in LOOSE_INDEX_HEADING_RE.finditer(content)]
    malformed = [pos for pos in loose if pos not in strict]
    if malformed:
        line = content[malformed[0] :].splitlines()[0]
        raise GeneratorError(
            3, f"Malformed Entity Index heading '{line}'; use '## Entity Index'"
        )
    spans = []
    for match in INDEX_HEADING_RE.finditer(content):
        nxt = SECTION_END_RE.search(content, match.end())
        end = nxt.start() if nxt else len(content)
        spans.append((match.start(), end, match.group(0)))
    return spans


def previous_index_ids(content: str, spans) -> set:
    """Union of IDs across all Entity Index bodies; refuse a body it cannot read."""
    ids = set()
    for start, end, heading in spans:
        body = content[start + len(heading) : end]
        found = set(INDEX_ROW_ID_RE.findall(body))
        data_rows = [
            ln
            for ln in body.splitlines()
            if ln.startswith("|")
            and not re.match(r"^\|\s*-", ln)
            and not re.match(r"^\|\s*ID\s*\|", ln)
        ]
        if data_rows and not found:
            raise GeneratorError(
                3,
                f"Entity Index body under '{heading.strip()}' has table rows but no readable IDs",
            )
        ids |= found
    return ids


def build_manifest(content: str, entities, notes, warnings, allow_drop) -> str:
    """New manifest text, or GeneratorError(3) if previous IDs would be lost.

    The newline style of the manifest (LF or CRLF) is kept.
    """
    spans = find_index_spans(content)
    old_ids = previous_index_ids(content, spans)
    new_ids = {e["id"] for e in entities}
    missing = old_ids - new_ids
    if missing != set(allow_drop):
        raise GeneratorError(
            3,
            "Entity Index guard: IDs that would disappear: "
            + (", ".join(sorted(missing)) or "none")
            + "; --allow-drop given: "
            + (", ".join(sorted(allow_drop)) or "none")
            + ". They must match exactly.",
        )

    today = date.today().isoformat()
    heading = spans[0][2] if spans else "## Entity Index"
    index = (
        generate_entity_index(entities, notes, warnings, heading)
        + f"\n\n> *Auto-generated by `generate-map.py` on {today}*\n\n"
    )
    newline = "\r\n" if "\r\n" in content else "\n"
    index = index.replace("\n", newline)
    rule = f"---{newline}{newline}"
    if spans:
        out = []
        pos = 0
        for i, (start, end, _) in enumerate(spans):
            out.append(content[pos:start])
            if i == 0:
                out.append(index)
            # A horizontal rule closing an old section belongs to the layout.
            if TRAILING_RULE_RE.search(content[start:end]):
                out.append(rule)
            pos = end
        out.append(content[pos:])
        return "".join(out)
    anchor = INSERT_ANCHOR_RE.search(content)
    if anchor:
        return content[: anchor.start()] + index + content[anchor.start() :]
    return content.rstrip() + newline + newline + index


def resolve_map_target(pack_dir: Path, map_id: str) -> tuple[Path, str | None]:
    """Return (path, created) for the map, or GeneratorError(2)."""
    map_dir = pack_dir / "07-map"
    by_id: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    unidentified: list[Path] = []
    if map_dir.is_dir():
        for md_file in sorted(map_dir.glob("*.md")):
            if md_file.name.startswith("_"):
                continue
            state, data, _ = read_frontmatter(md_file)
            if state == "invalid":
                raise GeneratorError(2, f"Unparsable frontmatter in map file {md_file}")
            if state == "ok" and data.get("id") not in (None, ""):
                by_id[str(data["id"])].append((md_file, data))
            else:
                unidentified.append(md_file)

    prefix = map_id.rsplit(".", 1)[0] + "."
    number_re = re.compile(re.escape(prefix) + r"([0-9]+)$")
    used = {int(m.group(1)) for i in by_id if (m := number_re.match(i))}
    free = next(n for n in range(1, len(used) + 2) if n not in used)
    hint = f"next free ID: {prefix}{free:03d}"

    owners = by_id.get(map_id, [])
    if len(owners) > 1:
        paths = ", ".join(str(p) for p, _ in owners)
        raise GeneratorError(2, f"Two map files share {map_id}: {paths}; {hint}")
    if owners:
        path, data = owners[0]
        if not data.get("generated"):
            raise GeneratorError(
                2,
                f"{map_id} belongs to a hand-written map {path}; pass --map-id ({hint})",
            )
        created = data.get("created")
        return path, str(created) if created else None
    if unidentified:
        # A map without an `id` may be a hand-written map that lost its header;
        # creating a new auto-map next to it could duplicate its ID.
        paths = ", ".join(str(p) for p in unidentified)
        raise GeneratorError(
            2, f"Map files without `id`: {paths}; add one before a new map is created"
        )
    path = map_dir / f"{map_id}.md"
    if path.exists():
        raise GeneratorError(
            2, f"{path} exists with another ID; pass --map-id ({hint})"
        )
    return path, None


def detect_domain(pack_dir: Path) -> str:
    """Detect domain code from manifest."""
    manifest = pack_dir / "00-pack-manifest.md"
    if manifest.exists():
        state, data, content = read_frontmatter(manifest)
        if state == "ok" and "pack_id" in data:
            return str(data["pack_id"])
        match = re.search(r"Pack ID[*]*:\s*`?([A-Z]{2,4})`?", content)
        if match:
            return match.group(1)
    for md_file in iter_pack_files(pack_dir):
        fm = parse_frontmatter(md_file)
        if fm:
            return fm["id"].split(".")[0]
    return pack_dir.name.upper()[:2]


def run(
    pack_dir: Path,
    update_manifest: bool,
    index_only: bool,
    map_id: str | None,
    allow_drop,
) -> None:
    domain = detect_domain(pack_dir)
    print(f"Domain: {domain}")
    print(f"Pack directory: {pack_dir}")

    entities, notes, warnings, quality_warnings = collect_entities(pack_dir)

    map_path = map_content = None
    if not index_only:
        map_id = map_id or f"{domain}.MAP.001"
        map_path, created = resolve_map_target(pack_dir, map_id)
        # The map indexes itself with the fields it is about to be written with,
        # so the first run already gives the final result.
        map_fields = {
            "name": "Pack Navigation Map",
            "summary": MAP_SUMMARY,
            "status": "—",
        }
        own = [e for e in entities if e["id"] == map_id and e["_source"] == "file"]
        if own:
            own[0].update(map_fields)
        else:
            entities.append({"id": map_id, "_source": "file", **map_fields})
        quality_warnings = [
            w
            for w in quality_warnings
            if not w.startswith(f"Missing `summary`: {map_id} ")
        ]
        map_content = generate_map(
            entities,
            warnings + quality_warnings,
            map_id,
            created or date.today().isoformat(),
        )

    manifest = pack_dir / "00-pack-manifest.md"
    new_manifest = None
    if update_manifest or index_only:
        if not manifest.exists():
            raise GeneratorError(1, f"Manifest not found: {manifest}")
        with manifest.open(encoding="utf-8", newline="") as f:
            old_manifest = f.read()
        new_manifest = build_manifest(
            old_manifest, entities, notes, warnings, allow_drop
        )

    # All refusals happened above; only now touch the disk. Both files are
    # staged as temp files first, so an I/O error leaves neither half-written.
    staged = []
    if map_content is not None:
        map_path.parent.mkdir(exist_ok=True)
        staged.append((map_path, map_content))
    if new_manifest is not None:
        staged.append((manifest, new_manifest))
    temps = []
    try:
        for target, text in staged:
            tmp = target.with_name(f".{target.name}.tmp")
            with tmp.open("w", encoding="utf-8", newline="") as f:
                f.write(text)
            temps.append((tmp, target))
    except OSError:
        for tmp, _ in temps:
            tmp.unlink(missing_ok=True)
        raise
    for tmp, target in temps:
        tmp.replace(target)
        print(f"Written: {target}")
    print(generate_entity_index(entities, notes, warnings))


def main():
    parser = argparse.ArgumentParser(
        description="SPF Pack map and Entity Index generator"
    )
    parser.add_argument("pack_dir")
    parser.add_argument(
        "--manifest", action="store_true", help="also update the manifest index"
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="update the manifest index only; do not write any map",
    )
    parser.add_argument(
        "--map-id", help="ID of the generated map (default <DOMAIN>.MAP.001)"
    )
    parser.add_argument(
        "--allow-drop",
        default="",
        help="comma-separated IDs allowed to leave the index",
    )
    args = parser.parse_args()

    pack_dir = Path(args.pack_dir).resolve()
    if not pack_dir.is_dir():
        print(f"Error: {pack_dir} is not a directory", file=sys.stderr)
        sys.exit(1)
    allow_drop = [i.strip() for i in args.allow_drop.split(",") if i.strip()]
    try:
        run(pack_dir, args.manifest, args.index_only, args.map_id, allow_drop)
    except GeneratorError as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(err.code)


if __name__ == "__main__":
    main()
