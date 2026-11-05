#!/usr/bin/env python3
"""Closed-loop tests for generate-map.py (WP-7 Ф297).

Run: python3 -m pytest SPF/scripts/test-generate-map.py
Each test builds a throwaway pack in a temp dir and checks the files written
(or not written) and the exit code.
"""

import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent
GENERATOR = SCRIPTS / "generate-map.py"
SPEC_001 = SCRIPTS.parent / "spec" / "SPF.SPEC.001-entity-coding.md"

MANIFEST_HEAD = "---\npack_id: XX\n---\n\n# Pack XX\n\n## Scope\n\nScope text.\n\n"
MANIFEST_TAIL = "## Changelog\n\n- 0.1 first\n"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return path


def entity(pack: Path, rel: str, eid: str, extra: str = "") -> Path:
    return write(
        pack / rel,
        f"---\nid: {eid}\nname: Name {eid}\nsummary: S {eid}\nstatus: active\n{extra}---\n\nBody.\n",
    )


def run(pack: Path, *args):
    return subprocess.run(
        [sys.executable, str(GENERATOR), str(pack), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def index_rows(manifest: Path):
    return re.findall(
        r"^\| ([A-Z]+(?:\.[A-Z]+)+\.\d+) \|", manifest.read_text(), re.MULTILINE
    )


def snapshot(pack: Path):
    return {p: p.read_bytes() for p in pack.rglob("*") if p.is_file()}


@pytest.fixture
def pack(tmp_path):
    p = tmp_path / "pack"
    write(p / "00-pack-manifest.md", MANIFEST_HEAD + MANIFEST_TAIL)
    entity(p, "03-methods/XX.M.001-a.md", "XX.M.001")
    return p


# A. Sections of *distinctions.md are indexed, with the ID from the capture group.
def test_a_distinction_sections_indexed(pack):
    write(
        pack / "01-domain-contract/01B-distinctions.md",
        """
        # Distinctions

        ### XX.D.010: Alpha ≠ Beta

        text

        ## [XX.D.011] Gamma ≠ Delta
        """,
    )
    r = run(pack, "--manifest")
    assert r.returncode == 0, r.stderr
    text = (pack / "00-pack-manifest.md").read_text()
    assert (
        "| XX.D.010 | Alpha ≠ Beta | D | Раздел в 01-domain-contract/01B-distinctions.md |"
        in text
    )
    assert "| XX.D.011 | Gamma ≠ Delta | D |" in text
    assert index_rows(pack / "00-pack-manifest.md").count("XX.D.011") == 1
    assert "| [XX.D.011]" not in text and "| XX.D.011]" not in text


# B. Legacy KIND.DOMAIN form is classified by its first part.
def test_b_legacy_kind_domain_form(pack):
    write(pack / "01-domain-contract/01B-distinctions.md", "### D.XX.001: Old form\n")
    assert run(pack, "--manifest").returncode == 0
    assert "| D.XX.001 | Old form | D |" in (pack / "00-pack-manifest.md").read_text()


# C. Exact file/section collision: two rows, warning inside the index; stable on rerun.
def test_c_i_exact_collision_two_rows(pack):
    entity(pack, "02-distinctions/XX.D.018-file.md", "XX.D.018")
    write(
        pack / "01-domain-contract/01B-distinctions.md",
        "## [XX.D.018] — Section meaning\n",
    )
    assert run(pack, "--manifest").returncode == 0
    manifest = pack / "00-pack-manifest.md"
    assert index_rows(manifest).count("XX.D.018") == 2
    text = manifest.read_text()
    assert "Exact ID collision: XX.D.018" in text
    assert "| XX.D.018 | Section meaning | D | Раздел в" in text
    assert run(pack, "--manifest").returncode == 0
    assert index_rows(manifest).count("XX.D.018") == 2


# Swapped-format pair is reported, both rows kept; four-part IDs are not paired.
def test_swapped_pair_warning(pack):
    entity(pack, "02-distinctions/XX.D.001-file.md", "XX.D.001")
    entity(pack, "07-map/XX.MAP.BIND.001-db.md", "XX.MAP.BIND.001")
    write(pack / "01-domain-contract/01B-distinctions.md", "### D.XX.001: Legacy\n")
    assert run(pack, "--manifest").returncode == 0
    text = (pack / "00-pack-manifest.md").read_text()
    assert "Swapped-format ID pair: D.XX.001 and XX.D.001" in text
    rows = set(index_rows(pack / "00-pack-manifest.md"))
    assert {"D.XX.001", "XX.D.001", "XX.MAP.BIND.001"} <= rows
    assert "XX.MAP.BIND" not in text.split("### Warnings", 1)[1]


# D. Heading with a suffix is found and kept; the rest of the manifest is byte-identical.
def test_d_suffix_heading_and_bytes_outside(pack):
    before = (
        MANIFEST_HEAD
        + "## Entity Index (SPF.SPEC.003)\n\n| ID | Name |\n|---|---|\n| XX.M.001 | old |\n\n"
    )
    write(pack / "00-pack-manifest.md", before + MANIFEST_TAIL)
    r = run(pack, "--index-only")
    assert r.returncode == 0, r.stderr
    text = (pack / "00-pack-manifest.md").read_text()
    assert text.count("Entity Index") == 1
    assert text.startswith(MANIFEST_HEAD + "## Entity Index (SPF.SPEC.003)\n")
    assert text.endswith(MANIFEST_TAIL)


# E. --index-only writes no map at all.
def test_e_index_only_writes_no_map(pack):
    assert run(pack, "--index-only").returncode == 0
    assert not (pack / "07-map").exists()
    assert "XX.M.001" in index_rows(pack / "00-pack-manifest.md")


# F. A hand-written map holding the default ID blocks the run before any write.
def test_f_handwritten_map_blocks(pack):
    write(
        pack / "07-map/XX.MAP.001-matrix.md", "---\nid: XX.MAP.001\nname: Matrix\n---\n"
    )
    entity(pack, "07-map/XX.MAP.003-other.md", "XX.MAP.003")
    before = snapshot(pack)
    r = run(pack, "--manifest")
    assert r.returncode == 2
    assert "next free ID: XX.MAP.002" in r.stderr
    assert snapshot(pack) == before


def test_f_generated_map_rewritten_in_place(pack):
    write(
        pack / "07-map/XX.MAP.002-auto.md",
        "---\nid: XX.MAP.002\ncreated: 2026-01-01\ngenerated: true\n---\nold\n",
    )
    assert run(pack, "--manifest", "--map-id", "XX.MAP.002").returncode == 0
    files = sorted(p.name for p in (pack / "07-map").iterdir())
    assert files == ["XX.MAP.002-auto.md"]
    text = (pack / "07-map/XX.MAP.002-auto.md").read_text()
    assert "created: 2026-01-01" in text and "generated: true" in text


def test_f_two_maps_same_id_block(pack):
    for name in ("a", "b"):
        write(
            pack / f"07-map/XX.MAP.001-{name}.md",
            "---\nid: XX.MAP.001\ngenerated: true\n---\n",
        )
    before = snapshot(pack)
    r = run(pack, "--manifest")
    assert r.returncode == 2 and "share XX.MAP.001" in r.stderr
    assert snapshot(pack) == before


def test_f_unparsable_map_frontmatter_blocks(pack):
    write(pack / "07-map/broken.md", "---\nid: [unclosed\n---\n")
    before = snapshot(pack)
    assert run(pack, "--manifest").returncode == 2
    assert snapshot(pack) == before


# G. A second run changes nothing (map indexes itself from the first run on).
def test_g_idempotent(pack):
    write(pack / "01-domain-contract/01B-distinctions.md", "### XX.D.010: Alpha\n")
    assert run(pack, "--manifest").returncode == 0
    first = snapshot(pack)
    assert run(pack, "--manifest").returncode == 0
    assert snapshot(pack) == first


# H + J. Two index sections: IDs of both are guarded; a lost ID refuses the run.
def test_h_j_union_of_index_sections_guarded(pack):
    two = (
        MANIFEST_HEAD + "## Entity Index\n\n| ID | Name |\n|---|---|\n\n"
        "## Entity Index (SPF.SPEC.003)\n\n| ID | Name |\n|---|---|\n| XX.R.009 | gone |\n\n"
        + MANIFEST_TAIL
    )
    write(pack / "00-pack-manifest.md", two)
    before = snapshot(pack)
    r = run(pack, "--index-only")
    assert r.returncode == 3 and "XX.R.009" in r.stderr
    assert snapshot(pack) == before


def test_h_two_sections_collapse_to_one(pack):
    two = (
        MANIFEST_HEAD
        + "## Entity Index\n\n| ID | Name |\n|---|---|\n| XX.M.001 | a |\n\n"
        "## Entity Index (SPF.SPEC.003)\n\n| ID | Name |\n|---|---|\n| XX.M.001 | b |\n\n"
        + MANIFEST_TAIL
    )
    write(pack / "00-pack-manifest.md", two)
    assert run(pack, "--index-only").returncode == 0
    text = (pack / "00-pack-manifest.md").read_text()
    assert len(re.findall(r"^## Entity Index", text, re.MULTILINE)) == 1
    assert index_rows(pack / "00-pack-manifest.md") == ["XX.M.001"]
    assert text.endswith(MANIFEST_TAIL)


def test_j_allow_drop_must_match_exactly(pack):
    old = (
        MANIFEST_HEAD + "## Entity Index\n\n| ID | Name |\n|---|---|\n"
        "| XX.R.008 | gone |\n| XX.R.009 | gone |\n\n" + MANIFEST_TAIL
    )
    write(pack / "00-pack-manifest.md", old)
    before = snapshot(pack)
    assert run(pack, "--index-only", "--allow-drop", "XX.R.009").returncode == 3
    assert snapshot(pack) == before
    assert (
        run(pack, "--index-only", "--allow-drop", "XX.R.008,XX.R.009").returncode == 0
    )
    assert set(index_rows(pack / "00-pack-manifest.md")) == {"XX.M.001"}


def test_j_unreadable_index_body_refuses(pack):
    odd = (
        MANIFEST_HEAD
        + "## Entity Index\n\n| Код | Имя |\n|---|---|\n| xx-m-1 | thing |\n\n"
        + MANIFEST_TAIL
    )
    write(pack / "00-pack-manifest.md", odd)
    before = snapshot(pack)
    r = run(pack, "--index-only")
    assert r.returncode == 3 and "no readable IDs" in r.stderr
    assert snapshot(pack) == before


# K. ID headings outside *distinctions.md go to notes, by class; the map has no ID headings.
def test_k_notes_classes_and_map_headings(pack):
    entity(pack, "02-domain-entities/XX.R.001-role.md", "XX.R.001")
    write(pack / "02-domain-entities/XX.ROLES-summary.md", "## XX.R.001 Role\n")
    entity(pack, "03-methods/XX.M.002-fund.md", "XX.M.002", "")
    with (pack / "03-methods/XX.M.002-fund.md").open("a") as f:
        f.write("\n### D.FR.001\n\ntext\n")
    assert run(pack, "--manifest").returncode == 0
    manifest = pack / "00-pack-manifest.md"
    text = manifest.read_text()
    assert (
        "- XX.R.001 in 02-domain-entities/XX.ROLES-summary.md — heading of an already indexed file"
        in text
    )
    assert "- D.FR.001 in 03-methods/XX.M.002-fund.md — not a pack entity" in text
    assert "D.FR.001" not in index_rows(manifest)
    assert index_rows(manifest).count("XX.R.001") == 1
    map_text = (pack / "07-map/XX.MAP.001.md").read_text()
    assert not re.search(r"^#{2,3} +\[?[A-Z]+\.[A-Z]+\.\d+", map_text, re.MULTILINE)


# L. The frozen base kinds match the "Base types" table of SPF.SPEC.001.
def test_l_base_kinds_match_spec():
    spec = SPEC_001.read_text(encoding="utf-8")
    section = spec.split("### Base types", 1)[1].split("\n### ", 1)[0]
    spec_kinds = set(re.findall(r"^\| `([A-Z]+)` \|", section, re.MULTILINE))
    source = GENERATOR.read_text(encoding="utf-8")
    frozen = re.search(r"^BASE_KINDS = \((.*?)\)", source, re.MULTILINE).group(1)
    assert set(re.findall(r'"([A-Z]+)"', frozen)) == spec_kinds
    assert spec_kinds  # the table was found


# Missing-summary warnings go to the map only, not into the manifest index.
def test_quality_warnings_map_only(pack):
    write(pack / "03-methods/XX.M.009-bare.md", "---\nid: XX.M.009\n---\n")
    assert run(pack, "--manifest").returncode == 0
    assert "Missing `summary`" not in (pack / "00-pack-manifest.md").read_text()
    assert "Missing `summary`: XX.M.009" in (pack / "07-map/XX.MAP.001.md").read_text()


# A horizontal rule that closed the old index section is kept.
def test_trailing_rule_kept(pack):
    old = (
        MANIFEST_HEAD
        + "## Entity Index\n\n| ID | Name |\n|---|---|\n| XX.M.001 | a |\n\n---\n\n"
    )
    write(pack / "00-pack-manifest.md", old + MANIFEST_TAIL)
    assert run(pack, "--index-only").returncode == 0
    assert (
        (pack / "00-pack-manifest.md").read_text().endswith("---\n\n" + MANIFEST_TAIL)
    )
    first = (pack / "00-pack-manifest.md").read_bytes()
    assert run(pack, "--index-only").returncode == 0
    assert (pack / "00-pack-manifest.md").read_bytes() == first


# A map file without `id` blocks creating a new auto-map, not rewriting an existing one.
def test_map_without_id_blocks_new_map(pack):
    write(pack / "07-map/matrix.md", "# Matrix without header\n")
    before = snapshot(pack)
    r = run(pack, "--manifest")
    assert r.returncode == 2 and "without `id`" in r.stderr
    assert snapshot(pack) == before
    write(pack / "07-map/XX.MAP.001.md", "---\nid: XX.MAP.001\ngenerated: true\n---\n")
    assert run(pack, "--manifest").returncode == 0


# Review 01: anchors, spans, newlines, odd IDs.
def test_insert_without_index_ignores_h3_lookalike(pack):
    write(
        pack / "00-pack-manifest.md",
        MANIFEST_HEAD + "### Upstream notes\n\ntext\n\n" + MANIFEST_TAIL,
    )
    assert run(pack, "--index-only").returncode == 0
    first = (pack / "00-pack-manifest.md").read_text()
    assert len(re.findall(r"^## Entity Index$", first, re.MULTILINE)) == 1
    assert "### Upstream notes" in first
    assert first.index("## Entity Index") < first.index("## Changelog")
    assert run(pack, "--index-only").returncode == 0
    assert (pack / "00-pack-manifest.md").read_text() == first


def test_index_last_section_and_following_h1_kept(pack):
    body = "## Entity Index\n\n| ID | Name |\n|---|---|\n| XX.M.001 | a |\n"
    write(
        pack / "00-pack-manifest.md", MANIFEST_HEAD + body + "\n# Appendix\n\nkeep me\n"
    )
    assert run(pack, "--index-only").returncode == 0
    assert (
        (pack / "00-pack-manifest.md").read_text().endswith("# Appendix\n\nkeep me\n")
    )
    write(pack / "00-pack-manifest.md", MANIFEST_HEAD + body)
    assert run(pack, "--index-only").returncode == 0
    assert index_rows(pack / "00-pack-manifest.md") == ["XX.M.001"]


def test_four_part_ids_guarded(pack):
    entity(pack, "07-map/XX.MAP.BIND.001-db.md", "XX.MAP.BIND.001")
    assert run(pack, "--index-only").returncode == 0
    (pack / "07-map/XX.MAP.BIND.001-db.md").unlink()
    before = snapshot(pack)
    r = run(pack, "--index-only")
    assert r.returncode == 3 and "XX.MAP.BIND.001" in r.stderr
    assert snapshot(pack) == before


def test_crlf_manifest_keeps_crlf(pack):
    text = (
        MANIFEST_HEAD
        + "## Entity Index\n\n| ID | Name |\n|---|---|\n| XX.M.001 | a |\n\n"
        + MANIFEST_TAIL
    )
    (pack / "00-pack-manifest.md").write_bytes(text.replace("\n", "\r\n").encode())
    assert run(pack, "--index-only").returncode == 0
    out = (pack / "00-pack-manifest.md").read_bytes()
    assert b"\n" not in out.replace(b"\r\n", b"")
    assert out.endswith(MANIFEST_TAIL.replace("\n", "\r\n").encode())


def test_malformed_index_heading_refused(pack):
    bad = (
        MANIFEST_HEAD
        + "##Entity Index\n\n| ID |\n|---|\n| XX.M.009 |\n\n"
        + MANIFEST_TAIL
    )
    write(pack / "00-pack-manifest.md", bad)
    before = snapshot(pack)
    r = run(pack, "--index-only")
    assert r.returncode == 3 and "Malformed Entity Index heading" in r.stderr
    assert snapshot(pack) == before


def test_next_free_hint_ignores_odd_map_ids(pack):
    write(pack / "07-map/XX.MAP.001-matrix.md", "---\nid: XX.MAP.001\n---\n")
    entity(pack, "07-map/XX.MAP.BIND.002-db.md", "XX.MAP.BIND.002")
    write(pack / "07-map/draft.md", "---\nid: XX.MAP.draft\n---\n")
    r = run(pack, "--manifest")
    assert r.returncode == 2 and "next free ID: XX.MAP.002" in r.stderr


def test_empty_id_is_not_an_entity(pack):
    write(pack / "03-methods/empty.md", "---\nid:\nname: x\n---\n")
    assert run(pack, "--index-only").returncode == 0
    assert "| None |" not in (pack / "00-pack-manifest.md").read_text()


def test_rule_after_second_index_section_kept(pack):
    two = (
        MANIFEST_HEAD
        + "## Entity Index\n\n| ID |\n|---|\n| XX.M.001 |\n\n"
        + "## Entity Index (SPF.SPEC.003)\n\n| ID |\n|---|\n| XX.M.001 |\n\n---\n\n"
        + MANIFEST_TAIL
    )
    write(pack / "00-pack-manifest.md", two)
    assert run(pack, "--index-only").returncode == 0
    assert (
        (pack / "00-pack-manifest.md").read_text().endswith("---\n\n" + MANIFEST_TAIL)
    )


def test_own_heading_generated_and_duplicates(pack):
    write(
        pack / "03-methods/XX.M.003-own.md",
        "---\nid: XX.M.003\nsummary: s\n---\n\n## [XX.M.003] Own\n",
    )
    write(
        pack / "04-work-products/gen.md",
        "---\nid: XX.WP.001\nsummary: s\ngenerated: true\n---\n\n## XX.D.077 In generated\n",
    )
    write(pack / "01-domain-contract/01B-distinctions.md", "### XX.D.050: One\n")
    write(pack / "01-domain-contract/01C-distinctions.md", "### XX.D.050: Two\n")
    assert run(pack, "--manifest").returncode == 0
    manifest = pack / "00-pack-manifest.md"
    text = manifest.read_text()
    assert index_rows(manifest).count("XX.M.003") == 1
    assert "XX.D.077" not in text
    assert index_rows(manifest).count("XX.D.050") == 2
    assert "Exact ID collision: XX.D.050 appears 2 times" in text


def test_allow_drop_without_missing_refused(pack):
    assert run(pack, "--index-only").returncode == 0
    before = snapshot(pack)
    assert run(pack, "--index-only", "--allow-drop", "XX.M.001").returncode == 3
    assert snapshot(pack) == before


def test_unreadable_file_reported(pack):
    (pack / "03-methods/bad.md").write_bytes(b"---\nid: XX.M.010\n---\n\xff\xfe")
    assert run(pack, "--index-only").returncode == 0
    assert (
        "Unreadable file: 03-methods/bad.md"
        in (pack / "00-pack-manifest.md").read_text()
    )


# An existing auto-map from an older generator (no summary) converges in one run.
def test_old_auto_map_converges_in_one_run(pack):
    write(
        pack / "07-map/XX.MAP.001.md",
        "---\nid: XX.MAP.001\nname: Pack Navigation Map\ngenerated: true\n---\n",
    )
    assert run(pack, "--manifest").returncode == 0
    first = snapshot(pack)
    assert run(pack, "--manifest").returncode == 0
    assert snapshot(pack) == first
