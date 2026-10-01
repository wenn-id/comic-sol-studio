"""Engine-shaped test fixtures shared by the Studio suite.

These helpers were previously imported from the engine repository's own test
modules (`tests.test_validation`, `tests.test_handoff_lifecycle`,
`tests.test_finalization`, and `tests.support` in `wenn-id/comicsol`). Studio
now installs the engine only as the `comic-sol` wheel, which does not ship
engine tests, so the small fixture surface Studio relies on lives here. Keep
it byte-compatible with the pinned engine (`ENGINE_COMMIT`): the values are
canonical project inputs that the engine validates.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from comic_sol_product.engine import comic_sol
from comic_sol_product.engine.character_identity import IDENTITY_PACK_PATH, derive_identity_pack
from comic_sol_product.engine.comic_sol import layout_rects


def valid_manifest():
    template = files("comic_sol_product").joinpath("templates", "manifest.json")
    data = json.loads(template.read_text("utf-8"))
    data["project_id"] = "sunlight-courier"
    data["title"] = "Sunlight Courier"
    data["created_at"] = "2026-07-18T04:00:00Z"
    data["updated_at"] = "2026-07-18T04:01:00Z"
    data["input"]["source_sha256"] = "a" * 64
    data["settings"]["page_count"] = 1
    data["settings"]["panel_count"] = 1
    data["panels"] = ["p01-01"]
    return data


def valid_characters():
    return {
        "schema_version": "1.0",
        "characters": [
            {
                "id": "mira",
                "name": "Mira",
                "role": "courier",
                "age_band": "young-adult",
                "pronouns": "she/her",
                "visual_fingerprint": {
                    "silhouette": "short compact build",
                    "face": "round face",
                    "hair": "chin-length black bob",
                    "wardrobe": "cream jacket",
                    "palette": ["charcoal", "cream", "amber"],
                    "signature_props": ["courier bag"],
                    "invariants": ["amber scarf", "circular bag clasp"],
                    "avoid": ["logos", "generated text"],
                },
                "personality": ["resourceful"],
                "motivation": "finish delivery",
                "speech": "short practical sentences",
                "reference_path": "references/characters/mira.png",
            }
        ],
    }


def valid_story():
    scene = {
        "purpose": "launch the delivery",
        "location": "dispatch hall",
        "time": "artificial dusk",
        "characters": ["mira"],
        "continuity_anchor": "brass walls and amber strips",
    }
    first = {"id": "delivery-hall", **scene}
    second = {"id": "generator-shaft", **scene, "purpose": "resolve delivery"}
    return {
        "schema_version": "1.0",
        "title": "Sunlight Courier",
        "logline": "A courier delivers the last vial of sunlight.",
        "theme": "Hope is shared.",
        "tone": ["urgent", "tender"],
        "rating": "teen",
        "setting": "An underground city.",
        "beginning": "Mira receives the vial.",
        "turn": "A bridge collapses.",
        "climax": "Mira crosses the shaft.",
        "ending": "The city relights.",
        "scenes": [first, second],
    }


def valid_storyboard():
    return {
        "schema_version": "1.0",
        "pages": [
            {
                "number": 1,
                "layout": "full-page",
                "panels": [
                    {
                        "id": "p01-01",
                        "order": 1,
                        "scene_id": "delivery-hall",
                        "rect": layout_rects("full-page")[0],
                        "beat": "Mira catches the vial.",
                        "characters": ["mira"],
                        "shot": "wide establishing shot",
                        "composition": "Mira on right third with safe top-left",
                        "action": "Mira catches the vial.",
                        "expression": "focused surprise",
                        "lighting": "amber key light",
                        "continuity": ["mira:amber scarf"],
                        "negative": ["text", "speech bubbles", "watermark"],
                        "text": [
                            {
                                "id": "p01-01-t01",
                                "kind": "dialogue",
                                "speaker": "mira",
                                "content": "I have one delivery left.",
                                "anchor": "top-left",
                                "voice_source": "human",
                                "speaker_anchor": [0.7, 0.5],
                                "priority": 1,
                            }
                        ],
                    }
                ],
            }
        ],
    }


def planner_project(test_case: unittest.TestCase) -> tuple[Path, Path]:
    """Create a STORYBOARDED one-page planner project; return (root, project)."""
    temporary = tempfile.TemporaryDirectory()
    test_case.addCleanup(temporary.cleanup)
    root = Path(temporary.name)
    project = comic_sol.init_project(
        root,
        "Sunlight Courier",
        b"A courier carries the last light.",
        {"mode": "short_prompt", "language": "en"},
        page_count=1,
    )

    manifest = valid_manifest()
    manifest["project_id"] = project.name
    manifest["status"] = "STORYBOARDED"
    manifest["input"]["source_sha256"] = comic_sol.sha256_file(project / "source/input.txt")
    comic_sol.atomic_write_json(project / "project.json", manifest)
    comic_sol.atomic_write_json(project / "plan/story-plan.json", valid_story())
    comic_sol.atomic_write_json(project / "plan/character-bible.json", valid_characters())
    comic_sol.atomic_write_json(project / "plan/storyboard.json", valid_storyboard())
    comic_sol.atomic_write_json(
        project / IDENTITY_PACK_PATH,
        derive_identity_pack(valid_characters()),
    )
    (project / "prompts/references/mira.txt").write_text(
        "Mira identity reference, neutral pose, plain background.",
        encoding="utf-8",
    )
    (project / "prompts/panels/p01-01.txt").write_text(
        "Mira catches the last vial of sunlight in the dispatch hall.",
        encoding="utf-8",
    )
    return root, project


def bounded_tail_regions(project: Path, page_number: int) -> list[dict[str, object]]:
    """Build exact test-only tail regions from current storyboard and geometry."""
    storyboard = json.loads((Path(project) / "plan/storyboard.json").read_text("utf-8"))
    page = next(page for page in storyboard["pages"] if page.get("number") == page_number)
    regions: list[dict[str, object]] = []
    for panel in page["panels"]:
        geometry = json.loads(
            (Path(project) / f"panels/{panel['id']}/lettering.json").read_text("utf-8")
        )
        placed = {item["id"]: item for item in geometry["items"]}
        for item in panel["text"]:
            if item.get("kind") != "dialogue":
                continue
            tail = placed[item["id"]]["tail"]
            regions.append(
                {
                    "panel_id": panel["id"],
                    "text_id": item["id"],
                    "speaker": item["speaker"],
                    "voice_source": item["voice_source"],
                    "speaker_anchor": item["speaker_anchor"],
                    "tip": tail["tip"],
                    "result": "pass",
                }
            )
    return regions


def valid_page_reviewer_checks(project: Path, page_number: int):
    return [
        {
            "id": "face-action-obstruction",
            "result": "pass",
            "severity": "error",
            "evidence": "Reviewer inspected every panel region for face and action obstruction.",
            "method": "bounded-visual-review",
            "reviewer": "fixture-reviewer",
            "regions": [{"scope": "all-panels"}],
        },
        {
            "id": "bubble-tail-direction",
            "result": "pass",
            "severity": "error",
            "evidence": "Reviewer inspected every bubble tail against its intended speaker.",
            "method": "bounded-visual-review",
            "reviewer": "fixture-reviewer",
            "regions": bounded_tail_regions(project, page_number),
        },
        {
            "id": "accidental-text-watermark",
            "result": "pass",
            "severity": "error",
            "evidence": "Reviewer inspected the full page for accidental text and watermarks.",
            "method": "bounded-visual-review",
            "reviewer": "fixture-reviewer",
            "regions": [{"scope": "page"}],
        },
    ]
