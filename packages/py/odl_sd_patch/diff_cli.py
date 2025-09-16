"""CLI for generating diffs and KPI deltas."""
import json
import sys

from odl_sd_patch.diff_utils import generate_diff_summary


def main() -> None:
    data = json.load(sys.stdin)
    result = generate_diff_summary(data["source"], data["target"])
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
