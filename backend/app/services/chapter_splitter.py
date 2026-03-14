import re
from dataclasses import dataclass
from typing import Protocol

from app.utils.regex import FULL_TEXT_FLAG, FULL_TEXT_PATTERN, compile_regex


FULL_CHAPTER_TITLE = "\u5168\u6587"


class ChapterRuleLike(Protocol):
    regex_pattern: str
    flags: str


@dataclass(frozen=True, slots=True)
class ChapterSegment:
    chapter_index: int
    chapter_title: str
    start_offset: int
    end_offset: int


def split_book_into_chapters(text: str, rule: ChapterRuleLike) -> list[ChapterSegment]:
    if _is_full_text_rule(rule):
        return [_build_full_text_chapter(text)]

    regex = compile_regex(rule.regex_pattern, rule.flags)
    matches = [match for match in regex.finditer(text) if match.end() > match.start()]
    if not matches:
        return [_build_full_text_chapter(text)]

    chapters: list[ChapterSegment] = []
    for index, match in enumerate(matches):
        start_offset = 0 if index == 0 else match.start()
        end_offset = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chapters.append(
            ChapterSegment(
                chapter_index=index,
                chapter_title=match.group(0).strip(),
                start_offset=start_offset,
                end_offset=end_offset,
            )
        )

    return chapters


def _build_full_text_chapter(text: str) -> ChapterSegment:
    return ChapterSegment(
        chapter_index=0,
        chapter_title=FULL_CHAPTER_TITLE,
        start_offset=0,
        end_offset=len(text),
    )


def _is_full_text_rule(rule: ChapterRuleLike) -> bool:
    if rule.regex_pattern == FULL_TEXT_PATTERN:
        return True

    flag_tokens = [token.upper() for token in re.split(r"[|,\s]+", rule.flags.strip()) if token]
    return FULL_TEXT_FLAG in flag_tokens
