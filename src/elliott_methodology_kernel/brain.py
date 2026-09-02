"""Read-only observation of the protected Elliott Brain package."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_PROTECTED_ROOT = Path(r"C:\ElliottCodex\Brain_LOCKED")

REQUIRED_PROTECTED_FILES = (
    "AGENTS.md",
    "VERSION",
    "PACKAGE_MANIFEST.json",
    "docs/elliott/SOURCE_POLICY.md",
    "docs/elliott/MASTER_PROTOCOL.md",
    "docs/elliott/PATTERN_BRAIN.md",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md",
    "docs/elliott/EVIDENCE_BRAIN.md",
    "docs/elliott/DECISION_BRAIN.md",
    "docs/elliott/OUTPUT_CONTRACT.md",
    "docs/elliott/SOURCE_EVIDENCE_MAP.json",
    "schemas/ANALYSIS_OUTPUT_SCHEMA.json",
    "tools/tradingview/tool_contract.json",
)


class BrainIntegrityError(RuntimeError):
    """Raised when the protected package cannot be safely observed."""


@dataclass(frozen=True, slots=True)
class BrainFileObservation:
    relative_path: str
    size_bytes: int
    observed_sha256: str
    approved_sha256: str | None
    approved_size_bytes: int | None

    @property
    def matches_approved_metadata(self) -> bool | None:
        if self.approved_sha256 is None:
            return None
        return (
            self.observed_sha256 == self.approved_sha256
            and self.size_bytes == self.approved_size_bytes
        )


@dataclass(frozen=True, slots=True)
class BrainManifest:
    protected_root: str
    package_name: str
    version: str
    observed_at_utc: str
    package_manifest_observed_sha256: str
    files: tuple[BrainFileObservation, ...]

    @property
    def mismatches(self) -> tuple[str, ...]:
        return tuple(
            item.relative_path
            for item in self.files
            if item.matches_approved_metadata is False
        )

    @property
    def observed_hashes(self) -> dict[str, str]:
        return {item.relative_path: item.observed_sha256 for item in self.files}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _absolute_root(protected_root: str | Path) -> Path:
    root = Path(protected_root)
    if not root.is_absolute():
        raise BrainIntegrityError("Protected Brain root must be an absolute path.")
    if not root.is_dir():
        raise BrainIntegrityError(f"Protected Brain root does not exist: {root}")
    return root.resolve(strict=True)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrainIntegrityError(f"Cannot read protected JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BrainIntegrityError(f"Protected JSON must contain an object: {path}")
    return value


def load_brain_manifest(
    protected_root: str | Path = DEFAULT_PROTECTED_ROOT,
) -> BrainManifest:
    """Observe required protected files without writing or copying them."""
    root = _absolute_root(protected_root)
    missing = [name for name in REQUIRED_PROTECTED_FILES if not (root / name).is_file()]
    if missing:
        raise BrainIntegrityError(
            "Required protected Brain files are missing: " + ", ".join(missing)
        )

    version = (root / "VERSION").read_text(encoding="utf-8-sig").strip()
    if not version:
        raise BrainIntegrityError("Protected VERSION is empty.")

    package_manifest_path = root / "PACKAGE_MANIFEST.json"
    package_manifest = _read_json(package_manifest_path)
    manifest_version = package_manifest.get("version")
    if manifest_version != version:
        raise BrainIntegrityError(
            f"VERSION ({version}) differs from PACKAGE_MANIFEST.json ({manifest_version})."
        )

    approved_entries: dict[str, dict[str, Any]] = {}
    entries = package_manifest.get("files")
    if not isinstance(entries, list):
        raise BrainIntegrityError("PACKAGE_MANIFEST.json files must be an array.")
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            approved_entries[entry["path"].replace("\\", "/")] = entry

    observations: list[BrainFileObservation] = []
    for relative_path in REQUIRED_PROTECTED_FILES:
        normalized = relative_path.replace("\\", "/")
        path = root / relative_path
        approved = approved_entries.get(normalized)
        observations.append(
            BrainFileObservation(
                relative_path=normalized,
                size_bytes=path.stat().st_size,
                observed_sha256=sha256_file(path),
                approved_sha256=(approved or {}).get("sha256"),
                approved_size_bytes=(approved or {}).get("size_bytes"),
            )
        )

    result = BrainManifest(
        protected_root=str(root),
        package_name=str(package_manifest.get("package", "")),
        version=version,
        observed_at_utc=datetime.now(timezone.utc).isoformat(),
        package_manifest_observed_sha256=sha256_file(package_manifest_path),
        files=tuple(observations),
    )
    if result.mismatches:
        raise BrainIntegrityError(
            "Observed protected files differ from package-approved metadata: "
            + ", ".join(result.mismatches)
        )
    return result


def load_required_json(
    relative_path: str,
    protected_root: str | Path = DEFAULT_PROTECTED_ROOT,
) -> dict[str, Any]:
    """Read a required protected JSON file through a constrained interface."""
    normalized = relative_path.replace("\\", "/")
    if normalized not in REQUIRED_PROTECTED_FILES:
        raise BrainIntegrityError(f"Protected file is not in the required set: {relative_path}")
    root = _absolute_root(protected_root)
    return _read_json(root / normalized)

