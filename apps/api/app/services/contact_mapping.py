def split_name(
    full_name: str,
) -> tuple[str, str]:

    parts = full_name.strip().split()

    if not parts:
        return "", ""

    if len(parts) == 1:
        return parts[0], ""

    return (
        parts[0],
        " ".join(parts[1:]),
    )