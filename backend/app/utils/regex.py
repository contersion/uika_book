import re
from typing import Final


class RegexRuleError(ValueError):
    pass


FLAG_MAP: Final[dict[str, re.RegexFlag]] = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "x": re.VERBOSE,
}

NAMED_FLAG_MAP: Final[dict[str, re.RegexFlag]] = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
    "VERBOSE": re.VERBOSE,
}

FULL_TEXT_PATTERN: Final[str] = "__FULL_TEXT__"
FULL_TEXT_FLAG: Final[str] = "FULL_TEXT"
MAX_MATCH_ITEMS: Final[int] = 20


def compile_regex(pattern: str, flags: str) -> re.Pattern[str]:
    regex_flags, is_full_text = _parse_flags(flags)
    if is_full_text or pattern == FULL_TEXT_PATTERN:
        raise RegexRuleError("Full text mode does not compile a regular expression")

    try:
        return re.compile(pattern, regex_flags)
    except re.error as exc:
        raise RegexRuleError(f"Invalid regex pattern: {exc}") from exc


def test_rule_on_text(text: str, pattern: str, flags: str) -> dict[str, object]:
    _, is_full_text = _parse_flags(flags)
    if is_full_text or pattern == FULL_TEXT_PATTERN:
        if not text:
            return {"matched": False, "count": 0, "items": []}
        return {
            "matched": True,
            "count": 1,
            "items": [
                {
                    "text": text,
                    "start": 0,
                    "end": len(text),
                }
            ],
        }

    regex = compile_regex(pattern, flags)
    items: list[dict[str, object]] = []
    count = 0

    for match in regex.finditer(text):
        count += 1
        if len(items) < MAX_MATCH_ITEMS:
            items.append(
                {
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    return {
        "matched": count > 0,
        "count": count,
        "items": items,
    }


def _parse_flags(flags: str) -> tuple[re.RegexFlag, bool]:
    normalized = flags.strip()
    if not normalized:
        return re.NOFLAG, False

    regex_flags = re.NOFLAG
    is_full_text = False
    invalid_tokens: list[str] = []

    for token in re.split(r"[|,\s]+", normalized):
        if not token:
            continue

        upper_token = token.upper()
        if upper_token == FULL_TEXT_FLAG:
            is_full_text = True
            continue
        if upper_token in NAMED_FLAG_MAP:
            regex_flags |= NAMED_FLAG_MAP[upper_token]
            continue
        if all(character.lower() in FLAG_MAP for character in token):
            for character in token.lower():
                regex_flags |= FLAG_MAP[character]
            continue

        invalid_tokens.append(token)

    if invalid_tokens:
        raise RegexRuleError(f"Invalid regex flags: {', '.join(invalid_tokens)}")

    return regex_flags, is_full_text
