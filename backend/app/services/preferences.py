import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.preferences import UserPreferencesPatchRequest


# 用户偏好默认值：包含书架、阅读器与二次元 UI 主题设置
DEFAULT_USER_PREFERENCES = {
    "version": 1,
    "bookshelf": {
        "sort": "created_at",
        "search": "",
        "group_id": None,
        "page": 1,
        "page_size": None,
    },
    "reader": {
        "font_size": 19,
        "line_height": 1.95,
        "letter_spacing": 0.0,
        "paragraph_spacing": 1.0,
        "content_width": 72,
        "theme": "light",
        # 二次元 UI 主题默认值：樱花粉、大圆角、霞鹜文楷
        "theme_color": "#F4A4B4",
        "border_radius": "soft",
        "font_family": "lxgwwenkai",
    },
}

ALLOWED_BOOK_SORTS = {"created_at", "recent_read", "title"}
ALLOWED_READER_THEMES = {"light", "dark"}
# 二次元 UI 主题允许取值集合，用于归一化时校验
ALLOWED_UI_BORDER_RADIUS = {"soft", "standard"}
ALLOWED_UI_FONT_FAMILY = {"lxgwwenkai", "system"}


def get_user_preferences(user: User) -> tuple[dict[str, Any], bool]:
    raw_value = user.preferences_json
    has_saved_preferences = isinstance(raw_value, str) and raw_value.strip() != ""
    if not has_saved_preferences:
        return _clone_default_preferences(), False

    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return _clone_default_preferences(), True

    return _normalize_user_preferences(payload), True


def update_user_preferences(
    db: Session,
    user: User,
    payload: UserPreferencesPatchRequest,
) -> tuple[dict[str, Any], bool]:
    current_preferences, _ = get_user_preferences(user)
    merged_preferences = _deep_merge(
        current_preferences,
        payload.model_dump(exclude_unset=True),
    )
    normalized_preferences = _normalize_user_preferences(merged_preferences)
    user.preferences_json = json.dumps(
        normalized_preferences,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    db.commit()
    db.refresh(user)
    return normalized_preferences, True


def _normalize_user_preferences(payload: Any) -> dict[str, Any]:
    normalized = _clone_default_preferences()
    raw_payload = payload if isinstance(payload, Mapping) else {}
    normalized["version"] = DEFAULT_USER_PREFERENCES["version"]
    normalized["bookshelf"] = _normalize_bookshelf_preferences(raw_payload.get("bookshelf"))
    normalized["reader"] = _normalize_reader_preferences(raw_payload.get("reader"))
    return normalized


def _normalize_bookshelf_preferences(payload: Any) -> dict[str, Any]:
    normalized = dict(DEFAULT_USER_PREFERENCES["bookshelf"])
    raw_payload = payload if isinstance(payload, Mapping) else {}

    sort = raw_payload.get("sort")
    if sort in ALLOWED_BOOK_SORTS:
        normalized["sort"] = sort

    search = raw_payload.get("search")
    if isinstance(search, str):
        normalized["search"] = search.strip()[:200]

    normalized["group_id"] = _normalize_optional_positive_int(raw_payload.get("group_id"))
    normalized["page"] = _normalize_positive_int(raw_payload.get("page"), fallback=1)
    normalized["page_size"] = _normalize_optional_positive_int(raw_payload.get("page_size"), maximum=100)
    return normalized


def _normalize_reader_preferences(payload: Any) -> dict[str, Any]:
    normalized = dict(DEFAULT_USER_PREFERENCES["reader"])
    raw_payload = payload if isinstance(payload, Mapping) else {}

    normalized["font_size"] = int(_clamp_number(raw_payload.get("font_size"), 15, 32, normalized["font_size"]))
    normalized["line_height"] = round(_clamp_number(raw_payload.get("line_height"), 1.45, 2.6, normalized["line_height"]), 2)
    normalized["letter_spacing"] = round(_clamp_number(raw_payload.get("letter_spacing"), 0.0, 2.0, normalized["letter_spacing"]), 2)
    normalized["paragraph_spacing"] = round(
        _clamp_number(raw_payload.get("paragraph_spacing"), 0.0, 2.5, normalized["paragraph_spacing"]),
        2,
    )
    normalized["content_width"] = int(_clamp_number(raw_payload.get("content_width"), 56, 96, normalized["content_width"]))

    theme = raw_payload.get("theme")
    if theme in ALLOWED_READER_THEMES:
        normalized["theme"] = theme

    # 二次元 UI 主题字段归一化：非法值回退到默认值，确保前端始终拿到合法数据
    theme_color = raw_payload.get("theme_color")
    normalized["theme_color"] = _normalize_hex_color(theme_color, normalized["theme_color"])

    border_radius = raw_payload.get("border_radius")
    if border_radius in ALLOWED_UI_BORDER_RADIUS:
        normalized["border_radius"] = border_radius

    font_family = raw_payload.get("font_family")
    if font_family in ALLOWED_UI_FONT_FAMILY:
        normalized["font_family"] = font_family

    return normalized


def _clone_default_preferences() -> dict[str, Any]:
    return {
        "version": DEFAULT_USER_PREFERENCES["version"],
        "bookshelf": dict(DEFAULT_USER_PREFERENCES["bookshelf"]),
        "reader": dict(DEFAULT_USER_PREFERENCES["reader"]),
    }


def _deep_merge(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in patch.items():
        current_value = merged.get(key)
        if isinstance(current_value, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(current_value, value)
            continue
        merged[key] = value
    return merged


def _normalize_positive_int(value: Any, *, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        return value if value >= 1 else fallback
    if isinstance(value, float) and value.is_integer():
        return int(value) if value >= 1 else fallback
    return fallback


def _normalize_optional_positive_int(value: Any, *, maximum: int | None = None) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    normalized: int | None
    if isinstance(value, int):
        normalized = value if value >= 1 else None
    elif isinstance(value, float) and value.is_integer():
        normalized = int(value) if value >= 1 else None
    else:
        normalized = None

    if normalized is None:
        return None
    if maximum is not None and normalized > maximum:
        return None
    return normalized


def _clamp_number(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return fallback
    normalized = float(value)
    if normalized < minimum:
        return fallback
    if normalized > maximum:
        return fallback
    return normalized


def _normalize_hex_color(value: Any, fallback: str) -> str:
    """校验并归一化十六进制颜色值。

    仅接受 #RRGGBB 格式（大小写均可），非法输入回退到默认值。
    成功校验后统一返回小写格式，避免前端因大小写差异产生重复渲染。
    """
    if not isinstance(value, str):
        return fallback
    # 去除首尾空白，防止用户误输入空格导致校验失败
    trimmed = value.strip()
    if len(trimmed) == 7 and trimmed.startswith("#"):
        try:
            int(trimmed[1:], 16)
            return trimmed.lower()
        except ValueError:
            pass
    return fallback
