from __future__ import annotations

import json

from .common import repo_root
from .massive_validation_runner import legacy_builder_output_filter


def scan_docs():
    return legacy_builder_output_filter(repo_root() / "docs")


if __name__ == "__main__":
    print(json.dumps(scan_docs(), indent=2))
