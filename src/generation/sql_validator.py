import re

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "CREATE", "REPLACE", "TRUNCATE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "REINDEX",
}


class SQLValidationError(Exception):
    pass


def validate_readonly_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")

    if not re.match(r"^\s*(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        raise SQLValidationError(f"Seules les requêtes SELECT/WITH sont autorisées : {cleaned[:80]}")

    if ";" in cleaned:
        raise SQLValidationError("Plusieurs instructions SQL détectées, une seule requête autorisée")

    tokens = set(re.findall(r"\b[A-Za-z]+\b", cleaned.upper()))
    forbidden_found = tokens & FORBIDDEN_KEYWORDS
    if forbidden_found:
        raise SQLValidationError(f"Mots-clés interdits détectés : {sorted(forbidden_found)}")

    return cleaned