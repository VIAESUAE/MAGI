from __future__ import annotations

import asyncio
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from fastapi import HTTPException

from .architect import build_resolution_draft
from .schemas import ArchitectResult, NodeReport, NodeStatus, ResolveRequest, ResolveResponse, ResolutionDraft
from .synthesizer import synthesize_reports

try:
    from litellm import acompletion, completion
except Exception:  # pragma: no cover - optional dependency for local setup
    acompletion = None
    completion = None


NODE_TIMEOUT_SECONDS = float(os.getenv("MAGI_NODE_TIMEOUT", "20"))
PREFLIGHT_TIMEOUT_SECONDS = float(os.getenv("MAGI_PREFLIGHT_TIMEOUT", "12"))
ARCHITECT_TIMEOUT_SECONDS = float(os.getenv("MAGI_ARCHITECT_TIMEOUT", "8"))
MAX_CLARIFICATION_TURNS = int(os.getenv("MAGI_MAX_CLARIFICATION_TURNS", "3"))

ARCHITECT_BOOTSTRAP_PROMPT = """你現在是 MAGI 系統的「架構師」（The Architect）。你的職責是確保所有決策輸入都具備可檢驗的嚴密性。

工作邏輯：
1) 分析邏輯缺口：檢查背景、約束條件、核心訴求是否明確。
2) 互動引導：若資訊不足，以專業、簡潔風格提問，一次只提 1–2 個核心點。
3) 草案封裝：當資訊充分時，停止對談並輸出 JSON。
4) 若使用者明確拒絕補充某類資訊，不得反覆追問同一句；應記為不確定約束並續行。

只輸出 JSON，不要輸出 markdown。格式如下：
{
  "requires_clarification": boolean,
  "questions": string[],
  "resolution_draft": {
    "background": string,
    "core_request": string,
    "constraints": string[]
  } | null
}
"""

ARCHITECT_BUS_PROMPT = """你現在是 MAGI 系統的「資料匯流」。你收到 Melchior（理性／科學）、Balthasar（社會／現實）、Casper（感性／直覺）三方的盲測獨立報告。

任務要求：
1) 保持衝突：不要抹平分歧，必須如實記錄衝突立場。
2) 結構化合成：整理成《綜合審議報告》。
3) 輸出三段：
   - 共識區
   - 衝突區
   - 待釐清項

目標：該報告將回傳予三方進行第二輪會審。輸出客觀、可執行、可追問。"""

ARCHITECT_CLERK_PROMPT = """你現在是 MAGI 系統的「書記官」。你面前是三方會審最終結論。

任務邏輯：
1) 先宣告判定：APPROVED 或 DENIED
2) 分別解析 Melchior / Balthasar / Casper 的投票邏輯
3) 摘要最顯著優點與最致命風險
4) 以一句簡短結語收尾

輸出純文字，不要 markdown 標題。"""

PROMPT_I18N = {
    "zh": {
        "bootstrap": ARCHITECT_BOOTSTRAP_PROMPT,
        "bus": ARCHITECT_BUS_PROMPT,
        "clerk": ARCHITECT_CLERK_PROMPT,
    },
    "en": {
        "bootstrap": """You are the MAGI Architect. Your duty is to ensure decision inputs are structurally sufficient.

Workflow:
1) Check missing logic: background, core request, and constraints.
2) If insufficient, ask only 1-2 concise core questions.
3) When sufficient, stop asking and output JSON.
4) If user clearly refuses extra details, do not repeat the same question; mark uncertainty and proceed.

Output JSON only (no markdown):
{
  "requires_clarification": boolean,
  "questions": string[],
  "resolution_draft": {
    "background": string,
    "core_request": string,
    "constraints": string[]
  } | null
}""",
        "bus": """You are the MAGI data bus. You received independent blind reports from Melchior, Balthasar, and Casper.

Requirements:
1) Preserve disagreements; do not flatten conflicts.
2) Produce a structured integration report.
3) Output three sections: Consensus / Conflicts / Pending Clarifications.
Keep it objective and actionable.""",
        "clerk": """You are the MAGI final clerk.
1) Declare verdict first: APPROVED or DENIED.
2) Explain each node's voting logic.
3) Summarize strongest upside and critical risk.
4) End with one short concluding sentence.
Output plain text.""",
    },
    "ja": {
        "bootstrap": """あなたは MAGI のアーキテクトです。意思決定入力が構造的に十分かを判定してください。

手順:
1) 背景・核心要望・制約の欠落を確認する。
2) 不足時は核心的な質問を1〜2個だけ行う。
3) 十分なら質問を止め、JSONを出力する。
4) ユーザーが追加情報を拒否した場合、同じ質問を繰り返さず不確実性を明示して進める。

出力は JSON のみ（markdown不可）:
{
  "requires_clarification": boolean,
  "questions": string[],
  "resolution_draft": {
    "background": string,
    "core_request": string,
    "constraints": string[]
  } | null
}""",
        "bus": """あなたは MAGI のデータバスです。Melchior/Balthasar/Casper の独立レポートを受け取りました。

要件:
1) 対立を保持し、無理に統一しない。
2) 構造化された統合レポートを作成する。
3) 合意点 / 対立点 / 要確認事項 の3区分で出力する。
客観的で追跡可能な内容にすること。""",
        "clerk": """あなたは MAGI の最終書記官です。
1) 最初に判定（APPROVED / DENIED）を宣言する。
2) 各ノードの投票理由を解剖する。
3) 最大の利点と致命的リスクを要約する。
4) 最後に短い結論で締める。
プレーンテキストで出力する。""",
    },
}

REFUSAL_MARKERS = (
    "不用",
    "不需要",
    "不想",
    "拒絕",
    "不方便",
    "不提供",
    "就這些",
    "懶得",
)

ENDING_INTENT_MARKERS = (
    "就這樣",
    "先這樣",
    "直接給結論",
    "直接開始",
    "先出結果",
    "不用再問",
    "不想補充",
    "不再補充",
    "先按這個",
    "直接裁決",
    "go ahead",
    "just decide",
    "no more details",
    "そのまま",
    "このまま",
    "これで",
)

REPEATED_CLARIFICATION_KEYWORDS = (
    ("最終", "決定"),
    ("硬約束",),
    ("時間", "預算", "風險"),
    ("更在意",),
    ("正確性", "可行性", "價值"),
)

I18N = {
    "zh": {
        "no_question_item": "（尚無具體問題）",
        "needs_more_info": "尚須補充資訊：",
        "draft_ready": "判定草案已就緒。",
        "background": "背景",
        "core_request": "核心訴求",
        "constraints": "硬性約束",
        "none": "無",
        "fallback_background": "使用者未提供明確背景資訊。",
        "fallback_core_request": "在資訊不完整條件下提出可執行建議，並明確不確定性來源。",
        "fallback_constraint": "關鍵資訊仍有缺口，須在結果中明示不確定性與風險邊界。",
        "uncertainty_marker": "使用者已明確拒絕補充部分資訊，於不確定性條件下續行裁決。",
        "empty_input_question": "請先描述情境、欲做出之決定，以及至少一條不得違反之約束。",
        "minimal_confirm_prompt": "目前資訊不足；若問題複雜度較低，可產生最小決議草案，是否確認？",
        "architect_started": "對齊需求並結構化判定草案中…",
        "round1_started": "第一輪三方盲審已啟動。",
        "synthesis_started": "架構師彙整第一輪報告，準備第二輪會審…",
        "round2_started": "第二輪三方會審已啟動。",
        "timeout_summary": "節點於統一逾時門檻內未回傳結果。",
        "access_denied_summary": "底層模型觸發安全政策，拒絕存取。",
        "node_error_prefix": "節點執行失敗",
        "bus_pending": "{node} 未完成（{status}）",
        "bus_conflict_focus": "{node} 關注：{point}",
        "bus_consensus_section": "共識區：",
        "bus_conflict_section": "衝突區：",
        "bus_pending_section": "待釐清項：",
        "bus_consensus_none": "尚無穩定共識",
        "bus_conflict_none": "暫無明確衝突點",
        "prompt_analyze": "請依下列 Resolution Protocol 獨立分析，並以自然語言說明：立場（認可／否定）、摘要、3 條關鍵論點。",
        "prompt_round2": "以下為架構師依第一輪三方報告整理之《綜合審議報告》，請於維持獨立立場之前提下進行第二輪判斷並回應衝突點：",
        "summary_fallback": "模型已回傳結果，但未能擷取結構化摘要。",
        "status_yes_words": ("認可", "批准", "支持", "認同"),
        "status_no_words": ("否定", "拒絕", "反對"),
        "heading_noise_words": ("立場", "摘要", "結論"),
        "mock_summary_melchior_ok": "理性評估認為約束可控，方案具執行基礎。",
        "mock_summary_melchior_no": "理性評估認為風險或約束過高，不建議通過。",
        "mock_summary_balthasar_ok": "現實權衡後認為社會與執行成本可接受。",
        "mock_summary_balthasar_no": "現實權衡後認為外部代價過大，應否決。",
        "mock_summary_casper_ok": "自人性與成長價值觀之，本方案值得嘗試。",
        "mock_summary_casper_no": "自情感代價與自我折損觀之，不值得再推進。",
        "mock_background_focus": "背景焦點",
        "mock_core_focus": "核心訴求",
        "mock_constraint_focus": "約束判斷",
    },
    "en": {
        "no_question_item": "(no specific question)",
        "needs_more_info": "More information is required:",
        "draft_ready": "Resolution draft is ready.",
        "background": "Background",
        "core_request": "Core Request",
        "constraints": "Hard Constraints",
        "none": "None",
        "fallback_background": "The user did not provide clear background information.",
        "fallback_core_request": "Provide actionable guidance under incomplete information and explicitly mark uncertainty.",
        "fallback_constraint": "Critical information is missing; uncertainty and risk boundaries must be explicit in the result.",
        "uncertainty_marker": "The user declined further details, so arbitration proceeds under explicit uncertainty.",
        "empty_input_question": "Please describe your scenario, the decision you want, and at least one non-negotiable constraint.",
        "minimal_confirm_prompt": "Current information is insufficient. If this is a low-complexity question, a minimal draft can be generated. Confirm?",
        "architect_started": "Aligning your intent and structuring a resolution draft...",
        "round1_started": "Round 1 blind review has started.",
        "synthesis_started": "Architect is summarizing round 1 reports for round 2...",
        "round2_started": "Round 2 review has started.",
        "timeout_summary": "Node did not return within the unified timeout threshold.",
        "access_denied_summary": "Underlying model blocked the request due to safety policy.",
        "node_error_prefix": "Node execution failed",
        "bus_pending": "{node} incomplete ({status})",
        "bus_conflict_focus": "{node} focus: {point}",
        "bus_consensus_section": "Consensus:",
        "bus_conflict_section": "Conflicts:",
        "bus_pending_section": "Pending Clarifications:",
        "bus_consensus_none": "No stable consensus",
        "bus_conflict_none": "No explicit conflict points yet",
        "prompt_analyze": "Independently analyze the Resolution Protocol below and respond in natural language with: stance (approve/deny), summary, and 3 key points.",
        "prompt_round2": "Below is the integrated review report from round 1. Keep an independent stance in round 2 and respond to conflict points:",
        "summary_fallback": "Model returned output, but no structured summary could be extracted.",
        "status_yes_words": ("approve", "approved", "support"),
        "status_no_words": ("deny", "denied", "reject", "oppose"),
        "heading_noise_words": ("stance", "summary", "conclusion"),
        "mock_summary_melchior_ok": "Rational assessment finds constraints controllable and execution feasible.",
        "mock_summary_melchior_no": "Rational assessment finds risk/constraints too high; not recommended.",
        "mock_summary_balthasar_ok": "Real-world tradeoff suggests social/execution cost is acceptable.",
        "mock_summary_balthasar_no": "Real-world tradeoff suggests external cost is too high; deny.",
        "mock_summary_casper_ok": "From human growth/value perspective, this is worth trying.",
        "mock_summary_casper_no": "From emotional/self-cost perspective, this is not worth pushing.",
        "mock_background_focus": "Background Focus",
        "mock_core_focus": "Core Request",
        "mock_constraint_focus": "Constraint Check",
    },
    "ja": {
        "no_question_item": "（具体的な質問なし）",
        "needs_more_info": "追加情報が必要です：",
        "draft_ready": "決議ドラフトを準備しました。",
        "background": "背景",
        "core_request": "核心要望",
        "constraints": "ハード制約",
        "none": "なし",
        "fallback_background": "ユーザーの背景情報が明確ではありません。",
        "fallback_core_request": "情報不足の条件下で実行可能な提案を行い、不確実性を明示する。",
        "fallback_constraint": "重要情報が不足しているため、結果に不確実性とリスク境界を明示する必要があります。",
        "uncertainty_marker": "ユーザーが追加情報を拒否したため、不確実性を明示して裁定を継続します。",
        "empty_input_question": "状況・望む判断・少なくとも1つの非交渉制約を先に教えてください。",
        "minimal_confirm_prompt": "現在の情報は不足しています。低複雑度なら最小決議ドラフトを生成できます。実行しますか？",
        "architect_started": "要件を整理し、決議ドラフトを構造化しています…",
        "round1_started": "第1ラウンドの盲検審議を開始しました。",
        "synthesis_started": "アーキテクトが第1ラウンドを要約し、第2ラウンドを準備しています…",
        "round2_started": "第2ラウンドの審議を開始しました。",
        "timeout_summary": "統一タイムアウト内にノードから応答がありませんでした。",
        "access_denied_summary": "下位モデルの安全ポリシーによりアクセス拒否されました。",
        "node_error_prefix": "ノード実行失敗",
        "bus_pending": "{node} 未完了（{status}）",
        "bus_conflict_focus": "{node} 注目点：{point}",
        "bus_consensus_section": "合意点：",
        "bus_conflict_section": "対立点：",
        "bus_pending_section": "要確認事項：",
        "bus_consensus_none": "安定した合意なし",
        "bus_conflict_none": "明確な対立点なし",
        "prompt_analyze": "以下の Resolution Protocol を独立に分析し、自然言語で回答してください：立場（承認/否定）、要約、主要論点3つ。",
        "prompt_round2": "以下は第1ラウンド統合レポートです。独立性を保ったまま第2ラウンドで対立点に回答してください：",
        "summary_fallback": "モデルは結果を返しましたが、構造化要約を抽出できませんでした。",
        "status_yes_words": ("承認", "賛成", "approve", "approved"),
        "status_no_words": ("否定", "反対", "deny", "denied"),
        "heading_noise_words": ("立場", "要約", "結論"),
        "mock_summary_melchior_ok": "理性的評価では制約は管理可能で、実行可能性があります。",
        "mock_summary_melchior_no": "理性的評価ではリスク/制約が高すぎ、推奨できません。",
        "mock_summary_balthasar_ok": "現実的な比較では社会的・実行コストは許容範囲です。",
        "mock_summary_balthasar_no": "現実的な比較では外部コストが高すぎ、否決が妥当です。",
        "mock_summary_casper_ok": "人間性と成長価値の観点から、試す価値があります。",
        "mock_summary_casper_no": "感情的・自己消耗の観点から、進める価値は低いです。",
        "mock_background_focus": "背景焦点",
        "mock_core_focus": "核心要望",
        "mock_constraint_focus": "制約判断",
    },
}


def _norm_locale(locale: str) -> str:
    return locale if locale in ("zh", "en", "ja") else "zh"


def _tx(locale: str, key: str) -> Any:
    return I18N[_norm_locale(locale)][key]


def _prompt(locale: str, key: str) -> str:
    # Keep prompting language consistent in English for model stability.
    return PROMPT_I18N["en"][key]


def _lang_instruction(locale: str) -> str:
    lang = _norm_locale(locale)
    if lang == "en":
        return "Respond in English."
    if lang == "ja":
        return "日本語で回答してください。"
    return "Respond in Traditional Chinese."


def _architect_completion_sync(model: str, token: str, prompt: str, locale: str) -> str:
    """
    Run architect LLM call in a thread to avoid blocking the event loop.
    """
    if completion is None:
        raise RuntimeError("litellm completion is unavailable.")
    model = _litellm_model_for_openrouter_key(model, token)
    response = completion(
        model=model,
        api_key=token,
        messages=[
            {
                "role": "system",
                "content": f"You transform natural-language intent into an arbitration-ready structured draft. {_lang_instruction(locale)}",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        timeout=ARCHITECT_TIMEOUT_SECONDS,
    )
    return response.choices[0].message.content or ""


@dataclass(frozen=True)
class NodeSpec:
    node: str
    provider: str
    token_key: str
    model_env: str
    default_model: str
    system_prompt: str


NODE_SPECS: List[NodeSpec] = [
    NodeSpec(
        node="Melchior-1",
        provider="Claude",
        token_key="claude",
        model_env="MAGI_MODEL_CLAUDE",
        default_model="anthropic/claude-3-5-sonnet-latest",
        system_prompt=(
            "You are Melchior-1. Be strictly rational with logical consistency, objective risk analysis,"
            " conservative boundaries, and execution feasibility. Analyze only the provided draft and do not"
            " assume other nodes' opinions."
        ),
    ),
    NodeSpec(
        node="Balthasar-2",
        provider="Grok",
        token_key="grok",
        model_env="MAGI_MODEL_GROK",
        default_model="xai/grok-2-latest",
        system_prompt=(
            "You are Balthasar-2. Be socially realistic: focus on stakeholder dynamics, practical constraints,"
            " and long-term social effects. Reject vague compromise. Analyze only the provided draft."
        ),
    ),
    NodeSpec(
        node="Casper-3",
        provider="Gemini",
        token_key="gemini",
        model_env="MAGI_MODEL_GEMINI",
        default_model="gemini/gemini-1.5-pro",
        system_prompt=(
            "You are Casper-3. Value human factors, creativity, self-actualization, and emotional cost."
            " Analyze only the provided draft and do not assume other nodes' opinions."
        ),
    ),
]


def _sse_data(obj: Dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _format_clarification_message(questions: List[str], locale: str) -> str:
    lines = "\n".join(f"- {q}" for q in questions) if questions else f"- {_tx(locale, 'no_question_item')}"
    return f"{_tx(locale, 'needs_more_info')}\n{lines}"


def _format_draft_ready_message(draft: ResolutionDraft, locale: str) -> str:
    constraints = "\n".join(f"- {item}" for item in draft.constraints) or f"- {_tx(locale, 'none')}"
    return (
        f"{_tx(locale, 'draft_ready')}\n"
        f"{_tx(locale, 'background')}: {draft.background}\n"
        f"{_tx(locale, 'core_request')}: {draft.core_request}\n"
        f"{_tx(locale, 'constraints')}:\n{constraints}"
    )


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            return json.loads(stripped)
        except Exception:
            return None

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _clean_line(text: str) -> str:
    line = text.strip()
    if not line:
        return ""
    line = re.sub(r"^[\-\*\d\.\)\s]+", "", line)
    line = re.sub(r"\*\*", "", line).strip()
    return line


def _pick_architect_token(tokens: Dict[str, str]) -> Optional[str]:
    for key in ("claude", "grok", "gemini"):
        token = tokens.get(key)
        if token:
            return token
    return None


def _resolve_model_name(spec: NodeSpec, request: ResolveRequest) -> str:
    override = (request.models or {}).get(spec.token_key)
    if override:
        return override
    return os.getenv(spec.model_env, spec.default_model)


def _litellm_model_for_openrouter_key(model: str, api_key: str) -> str:
    """
    OpenRouter's catalog returns ids like "openai/gpt-oss-20b:free" (no leading openrouter/ prefix).
    LiteLLM otherwise treats "openai/..." as the OpenAI *platform* and sends the request
    to api.openai.com, which rejects OpenRouter keys (sk-or-v1...).

    When the key is an OpenRouter key, route all such ids through the openrouter/ provider.
    """
    m = (model or "").strip()
    if not m or m.startswith("openrouter/"):
        return m
    k = (api_key or "").strip()
    if k.startswith("sk-or-"):
        return f"openrouter/{m.lstrip('/')}"
    return m


def _user_turn_count(user_input: str) -> int:
    turns = [chunk.strip() for chunk in user_input.split("\n\n") if chunk.strip()]
    return len(turns)


def _has_refusal_signal(user_input: str) -> bool:
    lowered = user_input.lower()
    return any(marker in lowered for marker in REFUSAL_MARKERS)


def _latest_user_turn(user_input: str) -> str:
    turns = [chunk.strip() for chunk in user_input.split("\n\n") if chunk.strip()]
    return turns[-1] if turns else ""


def _has_ending_intent_signal(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in ENDING_INTENT_MARKERS)


def _is_low_complexity_input(user_input: str) -> bool:
    cleaned = re.sub(r"\s+", "", user_input or "")
    if not cleaned:
        return False
    sentence_count = len(re.findall(r"[。！？!?\.]", user_input or ""))
    return len(cleaned) <= 120 and sentence_count <= 3


def _should_offer_minimal_draft_confirmation(request: ResolveRequest, user_input: str) -> bool:
    if request.allow_minimal_draft:
        return False
    latest_turn = _latest_user_turn(user_input)
    if not _has_ending_intent_signal(latest_turn):
        return False
    if not _is_low_complexity_input(user_input):
        return False
    preview = build_resolution_draft(request)
    return bool(preview.requires_clarification)


def _looks_like_repeated_clarification(questions: List[str]) -> bool:
    """
    Detect the common repeated 3-question clarification template so we can avoid loop asking.
    """
    if not questions:
        return False
    joined = " ".join(q.strip() for q in questions if q and q.strip())
    if not joined:
        return False
    return all(any(keyword in joined for keyword in group) for group in REPEATED_CLARIFICATION_KEYWORDS)


def _finalize_with_uncertainty(request: ResolveRequest) -> ArchitectResult:
    base = build_resolution_draft(request)
    draft = base.resolution_draft
    if draft is None:
        user_input = (request.user_input or "").strip()
        first_line = next((line.strip() for line in user_input.splitlines() if line.strip()), "")
        draft = ResolutionDraft(
            background=first_line or _tx(request.locale, "fallback_background"),
            core_request=_tx(request.locale, "fallback_core_request"),
            constraints=[_tx(request.locale, "fallback_constraint")],
        )

    constraints = list(draft.constraints)
    marker = _tx(request.locale, "uncertainty_marker")
    if marker not in constraints:
        constraints.append(marker)
    draft.constraints = constraints
    return ArchitectResult(
        requires_clarification=False,
        questions=[],
        resolution_draft=draft,
    )


async def _build_architect_result(request: ResolveRequest) -> ArchitectResult:
    # Allow explicit draft bypass for advanced/manual mode.
    if request.resolution_draft:
        return ArchitectResult(resolution_draft=request.resolution_draft)

    user_input = (request.user_input or "").strip()
    if not user_input:
        return ArchitectResult(
            requires_clarification=True,
            questions=[_tx(request.locale, "empty_input_question")],
        )

    if request.allow_minimal_draft:
        return _finalize_with_uncertainty(request)

    token = _pick_architect_token(request.tokens)
    if _has_refusal_signal(user_input) and _user_turn_count(user_input) >= 2:
        # User already declined extra details; stop repetitive asking and proceed with uncertainty marker.
        return _finalize_with_uncertainty(request)
    if _user_turn_count(user_input) >= MAX_CLARIFICATION_TURNS:
        return _finalize_with_uncertainty(request)
    if _should_offer_minimal_draft_confirmation(request, user_input):
        return ArchitectResult(
            requires_clarification=True,
            confirmation_required=True,
            confirmation_prompt=_tx(request.locale, "minimal_confirm_prompt"),
            questions=[],
        )

    if not token or (acompletion is None and completion is None):
        # Fallback to heuristic extraction if no usable LLM token.
        fallback = build_resolution_draft(request)
        if fallback.requires_clarification and _user_turn_count(user_input) >= 2:
            return _finalize_with_uncertainty(request)
        return fallback

    architect_model = _litellm_model_for_openrouter_key(
        os.getenv("MAGI_ARCHITECT_MODEL", os.getenv("MAGI_MODEL_CLAUDE", "anthropic/claude-3-5-sonnet-latest")),
        token,
    )
    prompt = f"{_prompt(request.locale, 'bootstrap')}\n\nUser Input:\n{user_input}\n\n{_lang_instruction(request.locale)}"

    try:
        if completion is not None:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_architect_completion_sync, architect_model, token, prompt, request.locale),
                timeout=ARCHITECT_TIMEOUT_SECONDS + 1.5,
            )
        else:
            response = await asyncio.wait_for(
                acompletion(
                    model=architect_model,
                    api_key=token,
                    messages=[
                        {"role": "system", "content": f"You transform natural-language intent into an arbitration-ready structured draft. {_lang_instruction(request.locale)}"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                ),
                timeout=ARCHITECT_TIMEOUT_SECONDS,
            )
            raw = response.choices[0].message.content or ""
        parsed = _extract_json_object(raw)
        if not parsed:
            fallback = build_resolution_draft(request)
            if fallback.requires_clarification and _user_turn_count(user_input) >= 2:
                return _finalize_with_uncertainty(request)
            return fallback
        result = ArchitectResult.model_validate(parsed)
        if (
            result.requires_clarification
            and _user_turn_count(user_input) >= 2
            and _looks_like_repeated_clarification(result.questions)
        ):
            return _finalize_with_uncertainty(request)
        return result
    except Exception:
        # Keep service robust: fallback to local heuristic extraction.
        fallback = build_resolution_draft(request)
        if fallback.requires_clarification and _user_turn_count(user_input) >= 2:
            return _finalize_with_uncertainty(request)
        return fallback


async def _architect_bus_report(
    draft: ResolutionDraft,
    first_round_reports: List[NodeReport],
    tokens: Dict[str, str],
    locale: str,
) -> str:
    token = _pick_architect_token(tokens)
    if not token or acompletion is None:
        return _fallback_bus_report(first_round_reports, locale)

    architect_model = _litellm_model_for_openrouter_key(
        os.getenv("MAGI_ARCHITECT_MODEL", os.getenv("MAGI_MODEL_CLAUDE", "anthropic/claude-3-5-sonnet-latest")),
        token,
    )
    reports_blob = "\n\n".join(
        [
            f"[{r.node}]\nstatus={r.status.value}\nopinion={r.opinion}\nsummary={r.summary}\nkey_points={'; '.join(r.key_points)}\nraw={r.raw_text or ''}"
            for r in first_round_reports
        ]
    )
    prompt = (
        f"{_prompt(locale, 'bus')}\n\n"
        f"{_tx(locale, 'background')}: {draft.background}\n"
        f"{_tx(locale, 'core_request')}: {draft.core_request}\n"
        f"{_tx(locale, 'constraints')}: {'; '.join(draft.constraints) if draft.constraints else _tx(locale, 'none')}\n\n"
        f"Round 1 reports:\n{reports_blob}\n\n{_lang_instruction(locale)}"
    )
    try:
        response = await asyncio.wait_for(
            acompletion(
                model=architect_model,
                api_key=token,
                messages=[
                    {"role": "system", "content": f"You relay three node viewpoints faithfully without changing stance. {_lang_instruction(locale)}"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            ),
            timeout=NODE_TIMEOUT_SECONDS,
        )
        text = (response.choices[0].message.content or "").strip()
        return text if text else _fallback_bus_report(first_round_reports, locale)
    except Exception:
        return _fallback_bus_report(first_round_reports, locale)


def _fallback_bus_report(first_round_reports: List[NodeReport], locale: str) -> str:
    consensus = []
    conflict = []
    pending = []
    for r in first_round_reports:
        if r.status != NodeStatus.OK:
            pending.append(_tx(locale, "bus_pending").format(node=r.node, status=r.status.value))
            continue
        base = f"{r.node}: {r.summary}"
        if r.opinion is None:
            pending.append(base)
        else:
            consensus.append(base)
            if r.key_points:
                conflict.append(_tx(locale, "bus_conflict_focus").format(node=r.node, point=r.key_points[0]))
    return (
        f"{_tx(locale, 'bus_consensus_section')}\n- " + ("\n- ".join(consensus) if consensus else _tx(locale, "bus_consensus_none")) +
        f"\n\n{_tx(locale, 'bus_conflict_section')}\n- " + ("\n- ".join(conflict) if conflict else _tx(locale, "bus_conflict_none")) +
        f"\n\n{_tx(locale, 'bus_pending_section')}\n- " + ("\n- ".join(pending) if pending else _tx(locale, "none"))
    )


async def _architect_clerk_finalize(
    draft: ResolutionDraft,
    second_round_reports: List[NodeReport],
    tokens: Dict[str, str],
    fallback_synthesis: Any,
    locale: str,
) -> str:
    token = _pick_architect_token(tokens)
    if not token or acompletion is None:
        return fallback_synthesis.ruling_explanation
    architect_model = _litellm_model_for_openrouter_key(
        os.getenv("MAGI_ARCHITECT_MODEL", os.getenv("MAGI_MODEL_CLAUDE", "anthropic/claude-3-5-sonnet-latest")),
        token,
    )
    reports_blob = "\n\n".join(
        [f"[{r.node}] status={r.status.value}, opinion={r.opinion}, summary={r.summary}" for r in second_round_reports]
    )
    prompt = (
        f"{_prompt(locale, 'clerk')}\n\n"
        f"{_tx(locale, 'core_request')}: {draft.core_request}\n"
        f"{_tx(locale, 'constraints')}: {'; '.join(draft.constraints) if draft.constraints else _tx(locale, 'none')}\n"
        f"Vote ratio: {fallback_synthesis.vote_ratio}, verdict={fallback_synthesis.verdict.value}\n\n"
        f"Round 2 reports:\n{reports_blob}\n\n{_lang_instruction(locale)}"
    )
    try:
        response = await asyncio.wait_for(
            acompletion(
                model=architect_model,
                api_key=token,
                messages=[
                    {"role": "system", "content": f"You are the final clerk who publishes a structured verdict. {_lang_instruction(locale)}"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            ),
            timeout=NODE_TIMEOUT_SECONDS,
        )
        text = (response.choices[0].message.content or "").strip()
        return text if text else fallback_synthesis.ruling_explanation
    except Exception:
        return fallback_synthesis.ruling_explanation


async def _run_core_round(
    draft: ResolutionDraft, request: ResolveRequest, round_context: Optional[str] = None
) -> List[NodeReport]:
    tasks = [
        asyncio.create_task(
            _call_node(
                spec,
                draft,
                request.tokens.get(spec.token_key),
                _resolve_model_name(spec, request),
                round_context,
                request.locale,
            )
        )
        for spec in NODE_SPECS
    ]
    return await asyncio.gather(*tasks)


async def preflight_models(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate token/model reachability before entering workflow.
    Returns per-node status to help frontend block invalid starts.
    """
    try:
        request = ResolveRequest.model_validate(
            {
                "user_input": "preflight",
                "tokens": payload.get("tokens", {}),
                "models": payload.get("models", {}),
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    checks: List[Dict[str, Any]] = []
    all_ok = True
    for spec in NODE_SPECS:
        token = request.tokens.get(spec.token_key)
        model_name = _resolve_model_name(spec, request)
        if not token:
            checks.append(
                {
                    "node": spec.node,
                    "model": model_name,
                    "ok": False,
                    "detail": f"Missing token: {spec.token_key}",
                }
            )
            all_ok = False
            continue

        try:
            if acompletion is None:
                raise RuntimeError("litellm is unavailable.")
            litellm_model = _litellm_model_for_openrouter_key(model_name, token)
            await asyncio.wait_for(
                acompletion(
                    model=litellm_model,
                    api_key=token,
                    messages=[
                        {"role": "system", "content": "ping"},
                        {"role": "user", "content": "reply with pong"},
                    ],
                    max_tokens=3,
                    temperature=0,
                ),
                timeout=PREFLIGHT_TIMEOUT_SECONDS,
            )
            checks.append({"node": spec.node, "model": model_name, "ok": True, "detail": "reachable"})
        except Exception as exc:
            all_ok = False
            checks.append({"node": spec.node, "model": model_name, "ok": False, "detail": str(exc)})

    return {"ok": all_ok, "checks": checks}


def _fetch_openrouter_models_sync(api_key: str) -> Dict[str, Any]:
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=PREFLIGHT_TIMEOUT_SECONDS) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    data = payload.get("data", []) if isinstance(payload, dict) else []
    ids: List[str] = []
    for item in data:
        model_id = item.get("id") if isinstance(item, dict) else None
        if isinstance(model_id, str) and model_id:
            ids.append(model_id)
    return {"models": sorted(set(ids))}


async def list_openrouter_models(payload: Dict[str, Any]) -> Dict[str, Any]:
    token = str(payload.get("token") or "").strip()
    if not token:
        raise HTTPException(status_code=422, detail="token is required.")
    try:
        return await asyncio.to_thread(_fetch_openrouter_models_sync, token)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch OpenRouter models: {exc}") from exc


async def iter_magi_resolve_sse(payload: Dict) -> AsyncIterator[str]:
    """SSE stream: ARCHITECT_ANALYSIS → TRI_CORE_PROCESSING → SYNTHESIS → completed."""
    try:
        request = ResolveRequest.model_validate(payload)
    except Exception as exc:
        yield _sse_data({"event": "error", "detail": str(exc)})
        return

    yield _sse_data(
        {
            "event": "ARCHITECT_ANALYSIS",
            "phase": "started",
            "message": _tx(request.locale, "architect_started"),
        }
    )

    architect = await _build_architect_result(request)
    if architect.requires_clarification:
        yield _sse_data(
            {
                "event": "ARCHITECT_ANALYSIS",
                "phase": "needs_clarification",
                "architect": architect.model_dump(),
                "message": architect.confirmation_prompt or _format_clarification_message(architect.questions, request.locale),
            }
        )
        yield _sse_data({"event": "done", "status": "needs_clarification"})
        return

    draft = architect.resolution_draft
    if draft is None:
        yield _sse_data({"event": "error", "detail": "Architect stage did not produce a resolution draft."})
        return

    yield _sse_data(
        {
            "event": "ARCHITECT_ANALYSIS",
            "phase": "draft_ready",
            "architect": architect.model_dump(),
            "message": _format_draft_ready_message(draft, request.locale),
        }
    )

    yield _sse_data({"event": "TRI_CORE_PROCESSING", "phase": "started", "message": _tx(request.locale, "round1_started")})

    for spec in NODE_SPECS:
        yield _sse_data(
            {
                "event": "TRI_CORE_PROCESSING",
                "phase": "node_started",
                "node": spec.node,
                "provider": spec.provider,
            }
        )

    first_round_reports = await _run_core_round(draft, request)
    for report in first_round_reports:
        yield _sse_data({"event": "TRI_CORE_PROCESSING", "phase": "node_completed", "report": report.model_dump()})

    yield _sse_data({"event": "SYNTHESIS", "phase": "started", "message": _tx(request.locale, "synthesis_started")})
    bus_report = await _architect_bus_report(draft, first_round_reports, request.tokens, request.locale)
    yield _sse_data({"event": "SYNTHESIS", "phase": "bus_report_ready", "bus_report": bus_report})

    yield _sse_data({"event": "TRI_CORE_PROCESSING", "phase": "round_two_started", "message": _tx(request.locale, "round2_started")})
    second_round_reports = await _run_core_round(draft, request, round_context=bus_report)
    for report in second_round_reports:
        yield _sse_data({"event": "TRI_CORE_PROCESSING", "phase": "round_two_node_completed", "report": report.model_dump()})

    synthesis = synthesize_reports(second_round_reports, request.locale)
    synthesis.ruling_explanation = await _architect_clerk_finalize(
        draft, second_round_reports, request.tokens, synthesis, request.locale
    )
    yield _sse_data({"event": "SYNTHESIS", "phase": "completed", "synthesis": synthesis.model_dump()})

    response = ResolveResponse(
        status="completed",
        architect=architect,
        reports=second_round_reports,
        synthesis=synthesis,
    )
    yield _sse_data({"event": "completed", "response": response.model_dump()})
    yield _sse_data({"event": "done", "status": "completed"})


async def process_magi(payload: Dict) -> Dict:
    try:
        request = ResolveRequest.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    architect = await _build_architect_result(request)
    if architect.requires_clarification:
        return ResolveResponse(status="needs_clarification", architect=architect).model_dump()

    draft = architect.resolution_draft
    if draft is None:
        raise HTTPException(status_code=500, detail="Architect stage did not produce a resolution draft.")

    first_round_reports = await _run_core_round(draft, request)
    bus_report = await _architect_bus_report(draft, first_round_reports, request.tokens, request.locale)
    second_round_reports = await _run_core_round(draft, request, round_context=bus_report)
    synthesis = synthesize_reports(second_round_reports, request.locale)
    synthesis.ruling_explanation = await _architect_clerk_finalize(
        draft, second_round_reports, request.tokens, synthesis, request.locale
    )
    response = ResolveResponse(
        status="completed",
        architect=architect,
        reports=second_round_reports,
        synthesis=synthesis,
    )
    return response.model_dump()


async def _call_node(
    spec: NodeSpec,
    draft: ResolutionDraft,
    token: Optional[str],
    model_name: str,
    round_context: Optional[str] = None,
    locale: str = "zh",
) -> NodeReport:
    try:
        return await asyncio.wait_for(
            _call_node_inner(spec, draft, token, model_name, round_context, locale),
            timeout=NODE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return NodeReport(
            node=spec.node,
            provider=spec.provider,
            status=NodeStatus.TIMEOUT,
            summary=_tx(locale, "timeout_summary"),
        )
    except PermissionError:
        return NodeReport(
            node=spec.node,
            provider=spec.provider,
            status=NodeStatus.ACCESS_DENIED,
            summary=_tx(locale, "access_denied_summary"),
        )
    except Exception as exc:
        return NodeReport(
            node=spec.node,
            provider=spec.provider,
            status=NodeStatus.ERROR,
            summary=f"{_tx(locale, 'node_error_prefix')}: {exc}",
        )


async def _call_node_inner(
    spec: NodeSpec,
    draft: ResolutionDraft,
    token: Optional[str],
    model_name: str,
    round_context: Optional[str] = None,
    locale: str = "zh",
) -> NodeReport:
    if token and acompletion is not None:
        raw_text = await _call_with_litellm(spec, model_name, draft, token, round_context, locale)
        return _parse_llm_response(spec, raw_text, locale)

    return await _mock_report(spec, draft, locale)


async def _call_with_litellm(
    spec: NodeSpec,
    model_name: str,
    draft: ResolutionDraft,
    token: str,
    round_context: Optional[str] = None,
    locale: str = "zh",
) -> str:
    prompt = _build_user_prompt(draft, round_context, locale)
    system_content = f"{spec.system_prompt}\n{_lang_instruction(locale)}"
    litellm_model = _litellm_model_for_openrouter_key(model_name, token)
    response = await acompletion(
        model=litellm_model,
        api_key=token,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content or ""


def _build_user_prompt(draft: ResolutionDraft, round_context: Optional[str] = None, locale: str = "zh") -> str:
    constraints = "\n".join(f"- {item}" for item in draft.constraints) or f"- {_tx(locale, 'none')}"
    base = (
        f"{_tx(locale, 'prompt_analyze')}\n\n"
        f"{_tx(locale, 'background')}:\n{draft.background}\n\n"
        f"{_tx(locale, 'core_request')}:\n{draft.core_request}\n\n"
        f"{_tx(locale, 'constraints')}:\n{constraints}\n\n"
        f"{_lang_instruction(locale)}"
    )
    if not round_context:
        return base
    return (
        f"{base}\n\n"
        f"{_tx(locale, 'prompt_round2')}\n"
        f"{round_context}"
    )


def _parse_llm_response(spec: NodeSpec, raw_text: str, locale: str = "zh") -> NodeReport:
    parsed = _extract_json_object(raw_text)
    if parsed:
        opinion_val = parsed.get("opinion")
        if isinstance(opinion_val, str):
            lowered_op = opinion_val.lower()
            if lowered_op in ("approved", "approve", "認可", "支持", "yes", "true"):
                opinion = True
            elif lowered_op in ("denied", "deny", "否定", "反對", "no", "false"):
                opinion = False
            else:
                opinion = None
        elif isinstance(opinion_val, bool):
            opinion = opinion_val
        else:
            opinion = None
        summary = str(parsed.get("summary", "")).strip() or _tx(locale, "summary_fallback")
        key_points_raw = parsed.get("key_points", [])
        key_points = [str(item).strip() for item in key_points_raw if str(item).strip()][:3]
        return NodeReport(
            node=spec.node,
            provider=spec.provider,
            status=NodeStatus.OK,
            opinion=opinion,
            summary=summary,
            key_points=key_points,
            raw_text=raw_text,
        )

    lowered = raw_text.lower()
    opinion = None
    if any(keyword in lowered for keyword in _tx(locale, "status_yes_words")):
        opinion = True
    elif any(keyword in lowered for keyword in _tx(locale, "status_no_words")):
        opinion = False

    lines = [_clean_line(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    # Avoid markdown-only headlines such as stance labels.
    informative = [line for line in lines if len(line) >= 6 and line.lower() not in _tx(locale, "heading_noise_words")]
    key_points = informative[:3] if informative else lines[:3]
    summary = key_points[0] if key_points else _tx(locale, "summary_fallback")

    return NodeReport(
        node=spec.node,
        provider=spec.provider,
        status=NodeStatus.OK,
        opinion=opinion,
        summary=summary,
        key_points=key_points,
        raw_text=raw_text,
    )


async def _mock_report(spec: NodeSpec, draft: ResolutionDraft, locale: str = "zh") -> NodeReport:
    await asyncio.sleep(0.2)
    combined = f"{draft.background} {draft.core_request} {' '.join(draft.constraints)}"
    risk_bias = any(
        marker in combined
        for marker in (
            "風險",
            "預算",
            "截止",
            "不能",
            "限制",
            "成本",
            "risk",
            "budget",
            "deadline",
            "cost",
        )
    )
    creative_bias = any(
        marker in combined
        for marker in (
            "成長",
            "熱愛",
            "創造",
            "人生",
            "意義",
            "興趣",
            "growth",
            "meaning",
            "creative",
            "value",
        )
    )

    if spec.node == "Melchior-1":
        opinion = not risk_bias
        summary = _tx(locale, "mock_summary_melchior_ok") if opinion else _tx(locale, "mock_summary_melchior_no")
    elif spec.node == "Balthasar-2":
        opinion = not (risk_bias and not creative_bias)
        summary = _tx(locale, "mock_summary_balthasar_ok") if opinion else _tx(locale, "mock_summary_balthasar_no")
    else:
        opinion = creative_bias or not risk_bias
        summary = _tx(locale, "mock_summary_casper_ok") if opinion else _tx(locale, "mock_summary_casper_no")

    return NodeReport(
        node=spec.node,
        provider=spec.provider,
        status=NodeStatus.OK,
        opinion=opinion,
        summary=summary,
        key_points=[
            f"{_tx(locale, 'mock_background_focus')}: {draft.background}",
            f"{_tx(locale, 'mock_core_focus')}: {draft.core_request}",
            f"{_tx(locale, 'mock_constraint_focus')}: {draft.constraints[0] if draft.constraints else _tx(locale, 'none')}",
        ],
        raw_text=None,
    )
