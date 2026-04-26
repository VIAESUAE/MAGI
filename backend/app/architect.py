from __future__ import annotations

import re
from typing import List

from .schemas import ArchitectResult, ResolutionDraft, ResolveRequest


ACTION_HINTS = (
    "想",
    "希望",
    "需要",
    "請",
    "幫我",
    "決定",
    "評估",
    "分析",
    "規劃",
    "方案",
    "want",
    "need",
    "please",
    "help",
    "decide",
    "evaluate",
    "analyze",
    "plan",
    "solve",
    "したい",
    "必要",
    "判斷",
    "評価",
    "分析",
    "計画",
    "方針",
)

CONSTRAINT_MARKERS = (
    "必須",
    "不能",
    "不要",
    "預算",
    "截止",
    "時間",
    "成本",
    "風險",
    "限制",
    "must",
    "cannot",
    "shouldn't",
    "deadline",
    "budget",
    "cost",
    "risk",
    "constraint",
    "制約",
    "必須",
    "禁止",
    "予算",
    "期限",
    "コスト",
    "リスク",
)

I18N_TEXT = {
    "zh": {
        "clarification_questions": [
            "你期望 MAGI 最終須幫你做成哪一項決定？",
            "此事有哪些不得違反之硬性約束，例如時間、預算、風險或立場？",
            "你較在意結果正確性、執行可行性，抑或個人價值與感受？",
        ],
        "fallback_constraint": "未明確提供硬性約束，裁決時須標示不確定性。",
    },
    "en": {
        "clarification_questions": [
            "What final decision do you want MAGI to make?",
            "What hard constraints cannot be violated, such as time, budget, risk, or stance?",
            "What matters most to you: correctness, execution feasibility, or personal values and feelings?",
        ],
        "fallback_constraint": "No explicit hard constraints were provided; uncertainty must be marked during arbitration.",
    },
    "ja": {
        "clarification_questions": [
            "MAGI に最終的にどのような判断をしてほしいですか？",
            "時間・予算・リスク・立場など、絶対に破れない制約は何ですか？",
            "重視するのは正確性、実行可能性、それとも個人の価値観・感情ですか？",
        ],
        "fallback_constraint": "明確なハード制約が不足しているため、裁定時に不確実性を明示する必要があります。",
    },
}


def _norm_locale(locale: str) -> str:
    return locale if locale in ("zh", "en", "ja") else "zh"


def _text(locale: str, key: str):
    lang = _norm_locale(locale)
    return I18N_TEXT[lang][key]


def build_resolution_draft(request: ResolveRequest) -> ArchitectResult:
    if request.resolution_draft:
        return ArchitectResult(resolution_draft=request.resolution_draft)

    user_input = (request.user_input or "").strip()
    if not _is_sufficient(user_input):
        return ArchitectResult(
            requires_clarification=True,
            questions=_text(request.locale, "clarification_questions"),
        )

    return ArchitectResult(
        resolution_draft=ResolutionDraft(
            background=_extract_background(user_input),
            core_request=_extract_core_request(user_input),
            constraints=_extract_constraints(user_input, request.locale),
        )
    )


def _is_sufficient(text: str) -> bool:
    if len(text) < 20:
        return False
    return any(marker in text for marker in ACTION_HINTS)


def _extract_background(text: str) -> str:
    parts = re.split(r"[。！？!?\n]", text)
    cleaned = [part.strip() for part in parts if part.strip()]
    return cleaned[0] if cleaned else text


def _extract_core_request(text: str) -> str:
    for marker in ACTION_HINTS:
        if marker in text:
            idx = text.find(marker)
            return text[idx:].strip()
    return text


def _extract_constraints(text: str, locale: str) -> List[str]:
    constraints: List[str] = []
    for chunk in re.split(r"[。！？!?\n；;]", text):
        sentence = chunk.strip()
        if sentence and any(marker in sentence for marker in CONSTRAINT_MARKERS):
            constraints.append(sentence)

    if not constraints:
        constraints.append(_text(locale, "fallback_constraint"))

    return constraints
