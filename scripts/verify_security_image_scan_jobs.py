import json
import sys
from collections.abc import Iterable


EXPECTED_IMAGE_SCAN_NAMES = frozenset(
    {
        "Container image scan (product-amd64)",
        "Container image scan (product-arm64)",
        "Container image scan (product-armv7)",
        "Container image scan (docker-build-input)",
        "Container image scan (docker-build-optimized-input)",
        "Container image scan (cross-builder-input)",
        "Container image scan (m4b-test)",
        "Container image scan (node-fixture)",
        "Container image scan (x86-handoff-fixture)",
        "Container image scan (python-fixture)",
        "Container image scan (qbittorrent-fixture)",
        "Container image scan (musl-handoff-fixture)",
    }
)


def normalized_scan_name(name: str, conclusion: object) -> str | None:
    reusable_workflow_prefix = "security / "
    if name.startswith(reusable_workflow_prefix):
        name = name.removeprefix(reusable_workflow_prefix)
    if name == "Container image scan (${{ matrix.image }})" and conclusion == "skipped":
        return None
    if name.startswith("Container image scan ("):
        return name
    return None


def verify_image_scan_jobs(jobs: Iterable[dict[str, object]]) -> None:
    selected = []
    for job in jobs:
        name = job.get("name")
        if not isinstance(name, str):
            continue
        conclusion = job.get("conclusion")
        normalized = normalized_scan_name(name, conclusion)
        if normalized is not None:
            selected.append((normalized, conclusion))

    actual_names = {name for name, _ in selected}
    if (
        len(selected) != len(EXPECTED_IMAGE_SCAN_NAMES)
        or actual_names != EXPECTED_IMAGE_SCAN_NAMES
        or any(conclusion != "success" for _, conclusion in selected)
    ):
        raise ValueError("expected exactly 12 successful base-controlled image scans")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_security_image_scan_jobs.py <jobs-json>")
    verify_image_scan_jobs(json.loads(sys.argv[1]))


if __name__ == "__main__":
    main()
