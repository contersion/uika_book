from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ChapterRule, User
from app.schemas.chapter_rule import ChapterRuleCreate, ChapterRuleUpdate


class ChapterRuleError(ValueError):
    pass


class ChapterRuleNotFoundError(ChapterRuleError):
    pass


class BuiltinRuleMutationError(ChapterRuleError):
    pass


@dataclass(frozen=True)
class BuiltinRuleDefinition:
    rule_name: str
    regex_pattern: str
    flags: str
    description: str
    is_default: bool = False


BUILTIN_RULES: tuple[BuiltinRuleDefinition, ...] = (
    BuiltinRuleDefinition(
        rule_name="中文章节规则",
        regex_pattern=r"^\s*第\s*[0-9零〇一二两三四五六七八九十百千万]+\s*[章节回篇]\s*.*$",
        flags="MULTILINE",
        description="匹配常见中文章节标题，例如 第1章、第十二章、第003章。",
        is_default=True,
    ),
    BuiltinRuleDefinition(
        rule_name="英文章节规则",
        regex_pattern=r"^\s*chapter\s+\d+\s*.*$",
        flags="IGNORECASE|MULTILINE",
        description="匹配英文章节标题，例如 Chapter 1、CHAPTER 12。",
    ),
    BuiltinRuleDefinition(
        rule_name="卷章混合规则",
        regex_pattern=r"^\s*第\s*[0-9零〇一二两三四五六七八九十百千万]+\s*卷\s+第\s*[0-9零〇一二两三四五六七八九十百千万]+\s*[章节回]\s*.*$",
        flags="MULTILINE",
        description="匹配卷章混合标题，例如 第1卷 第2章。",
    ),
    BuiltinRuleDefinition(
        rule_name="单章节全文模式",
        regex_pattern="__FULL_TEXT__",
        flags="FULL_TEXT",
        description="不进行正则切分，将整本书作为单章节处理。",
    ),
)


def seed_builtin_rules(db: Session) -> None:
    existing_by_name = {
        rule.rule_name: rule
        for rule in db.execute(select(ChapterRule).where(ChapterRule.is_builtin.is_(True))).scalars().all()
    }

    for definition in BUILTIN_RULES:
        rule = existing_by_name.get(definition.rule_name)
        if rule is None:
            db.add(
                ChapterRule(
                    user_id=None,
                    rule_name=definition.rule_name,
                    regex_pattern=definition.regex_pattern,
                    flags=definition.flags,
                    description=definition.description,
                    is_builtin=True,
                    is_default=definition.is_default,
                )
            )
        else:
            rule.is_builtin = True
            rule.regex_pattern = definition.regex_pattern
            rule.flags = definition.flags
            rule.description = definition.description

    db.commit()
    ensure_default_rule(db)


def list_rules(db: Session, user_id: int) -> list[ChapterRule]:
    statement = (
        select(ChapterRule)
        .where(or_(ChapterRule.is_builtin.is_(True), ChapterRule.user_id == user_id))
        .order_by(ChapterRule.is_builtin.desc(), ChapterRule.id.asc())
    )
    return list(db.execute(statement).scalars().all())


def get_visible_rule(db: Session, user_id: int, rule_id: int) -> ChapterRule | None:
    statement = select(ChapterRule).where(
        ChapterRule.id == rule_id,
        or_(ChapterRule.is_builtin.is_(True), ChapterRule.user_id == user_id),
    )
    return db.execute(statement).scalar_one_or_none()


def get_default_rule(db: Session, user_id: int) -> ChapterRule | None:
    return next((rule for rule in list_rules(db, user_id) if rule.is_default), None)


def create_rule(db: Session, user: User, payload: ChapterRuleCreate) -> ChapterRule:
    rule = ChapterRule(
        user_id=user.id,
        rule_name=payload.rule_name,
        regex_pattern=payload.regex_pattern,
        flags=payload.flags,
        description=payload.description,
        is_builtin=False,
        is_default=False,
    )
    db.add(rule)
    _flush_or_raise(db)

    if payload.is_default:
        set_rule_as_default(db, user.id, rule)

    _commit_or_raise(db)
    db.refresh(rule)
    return rule


def update_rule(db: Session, user: User, rule_id: int, payload: ChapterRuleUpdate) -> ChapterRule:
    rule = get_visible_rule(db, user.id, rule_id)
    if rule is None:
        raise ChapterRuleNotFoundError("Chapter rule not found")

    if rule.is_builtin:
        _update_builtin_rule(db, user.id, rule, payload)
    else:
        provided_fields = payload.model_fields_set
        if "rule_name" in provided_fields:
            rule.rule_name = payload.rule_name
        if "regex_pattern" in provided_fields:
            rule.regex_pattern = payload.regex_pattern
        if "flags" in provided_fields:
            rule.flags = payload.flags
        if "description" in provided_fields:
            rule.description = payload.description
        if "is_default" in provided_fields:
            if payload.is_default:
                set_rule_as_default(db, user.id, rule)
            else:
                rule.is_default = False

    _commit_or_raise(db)
    db.refresh(rule)
    ensure_default_rule(db)
    db.refresh(rule)
    return rule


def delete_rule(db: Session, user: User, rule_id: int) -> None:
    rule = get_visible_rule(db, user.id, rule_id)
    if rule is None:
        raise ChapterRuleNotFoundError("Chapter rule not found")
    if rule.is_builtin:
        raise BuiltinRuleMutationError("Built-in rules cannot be deleted")

    db.delete(rule)
    db.commit()
    ensure_default_rule(db)


def set_rule_as_default(db: Session, user_id: int, target_rule: ChapterRule) -> None:
    for rule in list_rules(db, user_id):
        rule.is_default = rule.id == target_rule.id


def ensure_default_rule(db: Session) -> None:
    visible_rules = list(
        db.execute(
            select(ChapterRule).where(or_(ChapterRule.is_builtin.is_(True), ChapterRule.user_id.is_not(None)))
        ).scalars().all()
    )
    if not visible_rules:
        return

    default_rules = [rule for rule in visible_rules if rule.is_default]
    if len(default_rules) == 1:
        return

    preferred_rule = next((rule for rule in visible_rules if rule.rule_name == "中文章节规则" and rule.is_builtin), visible_rules[0])
    for rule in visible_rules:
        rule.is_default = rule.id == preferred_rule.id
    db.commit()


def _update_builtin_rule(db: Session, user_id: int, rule: ChapterRule, payload: ChapterRuleUpdate) -> None:
    provided_fields = payload.model_fields_set
    core_fields_modified = any(field in provided_fields for field in ("rule_name", "regex_pattern", "flags", "description"))
    if core_fields_modified:
        raise BuiltinRuleMutationError("Built-in rules only allow updating the default status")

    if "is_default" in provided_fields:
        if payload.is_default:
            set_rule_as_default(db, user_id, rule)
        else:
            rule.is_default = False


def _flush_or_raise(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ChapterRuleError("Chapter rule name already exists") from exc


def _commit_or_raise(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ChapterRuleError("Chapter rule name already exists") from exc
