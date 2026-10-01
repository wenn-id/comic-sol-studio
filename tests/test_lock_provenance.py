"""Web lock provenance: every hash lock comes from `requirements/web.in`.

Ported from the engine repository's `tests/test_lock_provenance.py` when Studio
moved out of `wenn-id/comicsol`. The three platform locks must agree about the
package set and pinned versions, except for documented environment-marker
packages, and every direct pin in `web.in` must appear unchanged in each lock.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements"
LOCKS = REQUIREMENTS / "locks"
PLATFORMS = ("linux", "macos", "windows")
# The quality tool chain pulls `colorama` on Windows as a click dependency.
WEB_MARKER_PACKAGES = {
    "linux": frozenset(),
    "macos": frozenset(),
    "windows": frozenset({"colorama"}),
}


def pinned_requirement(line: str) -> tuple[str, str] | None:
    """Parse one exact `name==version` pin from a lock or input body line."""
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)", line)
    return (match.group(1).lower(), match.group(2)) if match else None


def body_pins(path: Path) -> dict[str, str]:
    """Return the exact pins declared by a file, ignoring comment lines."""
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        pin = pinned_requirement(line)
        if pin is not None:
            name, version = pin
            if name in pins and pins[name] != version:
                raise AssertionError(f"{path.name} pins {name} twice with different versions")
            pins[name] = version
    return pins


class WebLockProvenanceTests(unittest.TestCase):
    def lock(self, platform: str) -> Path:
        return LOCKS / f"web-{platform}-x86_64.txt"

    def test_every_platform_lock_names_web_in_as_its_input(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                header = self.lock(platform).read_text(encoding="utf-8")[:2000]
                self.assertIn("requirements/web.in", header)
                self.assertIn(f"web-{platform}-x86_64.txt", header)

    def test_direct_pins_appear_unchanged_in_every_lock(self):
        direct = body_pins(REQUIREMENTS / "web.in")
        self.assertTrue(direct)
        for platform in PLATFORMS:
            pins = body_pins(self.lock(platform))
            for name, version in direct.items():
                with self.subTest(platform=platform, package=name):
                    self.assertEqual(version, pins.get(name))

    def test_web_locks_differ_only_by_documented_windows_marker(self):
        reference = body_pins(self.lock("linux"))
        for platform in PLATFORMS[1:]:
            with self.subTest(platform=platform):
                pins = body_pins(self.lock(platform))
                allowed = WEB_MARKER_PACKAGES[platform]
                self.assertFalse(set(pins) - set(reference) - allowed)
                self.assertFalse(set(reference) - set(pins))
                for name in set(reference) & set(pins):
                    self.assertEqual(reference[name], pins[name], name)


if __name__ == "__main__":
    unittest.main()
