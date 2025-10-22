import re
from typing import Dict, Any

def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """
    Parse simple English phrases into filter params.
    Examples:
      "all single word palindromic strings" → {"word_count": 1, "is_palindrome": True}
      "strings longer than 10 characters"   → {"min_length": 11}
      "strings containing the letter z"     → {"contains_character": "z"}

    Raises:
      ValueError if query cannot be parsed.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")

    q = query.lower().strip()
    parsed = {}

    # --- Palindrome detection ---
    if re.search(r"\bpalindrom", q):
        parsed["is_palindrome"] = True

    # --- Word count ---
    if re.search(r"\b(single|one)\s+word\b", q):
        parsed["word_count"] = 1

    # --- Length filters (handle >= first) ---
    m = re.search(r"longer than or equal to (\d+)", q)
    if m:
        parsed["min_length"] = int(m.group(1))
    else:
        m = re.search(r"longer than (\d+)", q)
        if m:
            parsed["min_length"] = int(m.group(1)) + 1

    # --- Handle "at most" / "less than" phrases ---
    m = re.search(r"(?:less than|at most)\s+(\d+)", q)
    if m:
        parsed["max_length"] = int(m.group(1)) - 1

    # --- Generic "N characters" fallback ---
    m = re.search(r"(\d+)\s*characters?", q)
    if m and not any(kw in q for kw in ["longer", "shorter", "less", "at most"]):
        parsed["min_length"] = int(m.group(1))

    # --- Character containment ---
    if "first vowel" in q:
        parsed["contains_character"] = "a"
    else:
        m = re.search(r"contain(?:ing)? the letter (\w)", q)
        if m:
            parsed["contains_character"] = m.group(1)

    # --- Final check ---
    if not parsed:
        raise ValueError("Unable to parse natural language query")

    return parsed
