def parse_admin_ids(raw: str | None) -> set[int]:
    ids: set[int] = set()
    for part in (raw or "").replace(";", ",").split(","):
        value = part.strip()
        if not value:
            continue
        try:
            ids.add(int(value))
        except ValueError:
            continue
    return ids


def is_super_admin(user_id: int | None, raw_admin_ids: str | None) -> bool:
    return user_id is not None and user_id in parse_admin_ids(raw_admin_ids)
