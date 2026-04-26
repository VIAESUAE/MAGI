from __future__ import annotations

from typing import List

from .schemas import ConsensusVerdict, NodeReport, NodeStatus, SynthesisResult

I18N = {
    "zh": {
        "approve": "認可",
        "deny": "否定",
        "node_status": "{node} 為 {status}",
        "consensus_none": "沒有可用於仲裁之有效報告。",
        "disagreement_none": "三方均已回傳有效結果。",
        "ruling": "本輪裁決票型為 {approve}:{deny}。共識面：{consensus} 差異面：{disagreement}",
        "consensus_point": "{node} 傾向{stance}：{summary}",
        "sep": "；",
    },
    "en": {
        "approve": "APPROVE",
        "deny": "DENY",
        "node_status": "{node} is {status}",
        "consensus_none": "No valid reports were available for arbitration.",
        "disagreement_none": "All three nodes returned valid results.",
        "ruling": "Vote ratio is {approve}:{deny}. Consensus: {consensus} Difference: {disagreement}",
        "consensus_point": "{node} tends to {stance}: {summary}",
        "sep": "; ",
    },
    "ja": {
        "approve": "承認",
        "deny": "否定",
        "node_status": "{node} は {status}",
        "consensus_none": "裁定に使える有効レポートがありません。",
        "disagreement_none": "3ノードすべてが有効な結果を返しました。",
        "ruling": "今回の票型は {approve}:{deny}。合意点：{consensus} 相違点：{disagreement}",
        "consensus_point": "{node} は{stance}傾向：{summary}",
        "sep": "；",
    },
}


def _norm_locale(locale: str) -> str:
    return locale if locale in ("zh", "en", "ja") else "zh"


def synthesize_reports(reports: List[NodeReport], locale: str = "zh") -> SynthesisResult:
    lang = I18N[_norm_locale(locale)]
    valid_reports = [report for report in reports if report.status == NodeStatus.OK and report.opinion is not None]
    approve_count = sum(1 for report in valid_reports if report.opinion)
    deny_count = sum(1 for report in valid_reports if report.opinion is False)
    degraded_mode = len(valid_reports) != len(reports)

    if approve_count > deny_count:
        verdict = ConsensusVerdict.APPROVED
    else:
        verdict = ConsensusVerdict.DENIED

    consensus_points = [
        lang["consensus_point"].format(
            node=report.node,
            stance=lang["approve"] if report.opinion else lang["deny"],
            summary=report.summary,
        )
        for report in valid_reports
    ]
    degraded_points = [
        lang["node_status"].format(node=report.node, status=report.status.value)
        for report in reports
        if report.status != NodeStatus.OK
    ]

    consensus_summary = lang["sep"].join(consensus_points) if consensus_points else lang["consensus_none"]
    disagreement_summary = lang["sep"].join(degraded_points) if degraded_points else lang["disagreement_none"]

    ruling_explanation = lang["ruling"].format(
        approve=approve_count,
        deny=deny_count,
        consensus=consensus_summary,
        disagreement=disagreement_summary,
    )

    return SynthesisResult(
        verdict=verdict,
        vote_ratio=f"{approve_count}:{deny_count}",
        consensus_summary=consensus_summary,
        disagreement_summary=disagreement_summary,
        ruling_explanation=ruling_explanation,
        degraded_mode=degraded_mode,
    )
