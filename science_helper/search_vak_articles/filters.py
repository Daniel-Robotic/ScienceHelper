from typing import Any


def fizbuz(spec_line: str, targets: list[str]) -> bool:
    """Check if a specialty line starts with any of the target prefixes.

    Args:
        spec_line (str): A single specialty string.
        targets (list[str]): A list of target prefixes to match.

    Returns:
        bool: True if the spec_line starts with any of the target values, False otherwise.
    """
    return any(spec_line.startswith(t) for t in targets)


def filter_rows_by_specialty(
    rows: list[dict[str, Any]], targets: list[str]
) -> list[dict[str, Any]]:
    """Filter a list of rows by matching specialty prefixes.

    Each row is expected to contain a "specialties" field with a list of strings.
    If the `targets` list contains "all" (case-insensitive), no filtering is applied.

    Args:
        rows (list[dict[str, Any]]): List of dictionaries representing rows with a "specialties" key.
        targets (list[str]): List of specialty prefixes to filter by.

    Returns:
        list[dict[str, Any]]: Filtered list of rows where at least one specialty matches any target prefix.
    """  # noqa: E501
    if not targets or any(t.lower() == "all" for t in targets):
        return rows
    return [r for r in rows if any(fizbuz(sp, targets) for sp in r["specialties"])]
