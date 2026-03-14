from types import SimpleNamespace

from app.services.chapter_splitter import ChapterSegment, split_book_into_chapters
from app.utils.regex import FULL_TEXT_FLAG, FULL_TEXT_PATTERN


TEXT_WITH_CHAPTERS = "\u7b2c1\u7ae0 \u5f00\u59cb\n\u5185\u5bb9\u4e00\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u5185\u5bb9\u4e8c"
TEXT_WITH_PREFACE = "\u5e8f\u7ae0\n\u8bf4\u660e\n\u7b2c1\u7ae0 \u5f00\u59cb\n\u6b63\u6587\n\u7b2c2\u7ae0 \u7ee7\u7eed\n\u5c3e\u58f0"
TEXT_WITHOUT_MATCH = "\u8fd9\u662f\u4e00\u6bb5\u6ca1\u6709\u76ee\u5f55\u6807\u9898\u7684\u6b63\u6587\u3002"


def make_rule(pattern: str, flags: str = "") -> SimpleNamespace:
    return SimpleNamespace(regex_pattern=pattern, flags=flags)


def test_split_book_into_chapters_uses_matches_as_boundaries():
    second_start = TEXT_WITH_CHAPTERS.index("\u7b2c2\u7ae0 \u7ee7\u7eed")

    chapters = split_book_into_chapters(TEXT_WITH_CHAPTERS, make_rule(r"^\u7b2c\d+\u7ae0.*$", "m"))

    assert chapters == [
        ChapterSegment(
            chapter_index=0,
            chapter_title="\u7b2c1\u7ae0 \u5f00\u59cb",
            start_offset=0,
            end_offset=second_start,
        ),
        ChapterSegment(
            chapter_index=1,
            chapter_title="\u7b2c2\u7ae0 \u7ee7\u7eed",
            start_offset=second_start,
            end_offset=len(TEXT_WITH_CHAPTERS),
        ),
    ]


def test_split_book_into_chapters_keeps_leading_content_in_first_chapter():
    second_start = TEXT_WITH_PREFACE.index("\u7b2c2\u7ae0 \u7ee7\u7eed")

    chapters = split_book_into_chapters(TEXT_WITH_PREFACE, make_rule(r"^\u7b2c\d+\u7ae0.*$", "m"))

    assert chapters[0] == ChapterSegment(
        chapter_index=0,
        chapter_title="\u7b2c1\u7ae0 \u5f00\u59cb",
        start_offset=0,
        end_offset=second_start,
    )


def test_split_book_into_chapters_falls_back_to_single_chapter_when_no_match():
    chapters = split_book_into_chapters(TEXT_WITHOUT_MATCH, make_rule(r"^\u7b2c\d+\u7ae0.*$", "m"))

    assert chapters == [
        ChapterSegment(
            chapter_index=0,
            chapter_title="\u5168\u6587",
            start_offset=0,
            end_offset=len(TEXT_WITHOUT_MATCH),
        )
    ]


def test_split_book_into_chapters_handles_full_text_mode():
    chapters = split_book_into_chapters(TEXT_WITH_CHAPTERS, make_rule(FULL_TEXT_PATTERN, FULL_TEXT_FLAG))

    assert chapters == [
        ChapterSegment(
            chapter_index=0,
            chapter_title="\u5168\u6587",
            start_offset=0,
            end_offset=len(TEXT_WITH_CHAPTERS),
        )
    ]
