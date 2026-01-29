from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.services.levels_auto import get_cached_levels


@dataclass
class TechReport:
    score: float
    summary: str


@dataclass
class FundReport:
    score: float
    summary: str


@dataclass
class Decision:
    action: str
    entry: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    confidence: str
    invalidation: str
    tech: TechReport
    fund: FundReport


def technical_agent(symbol: str, tf: str, price: Optional[float]) -> TechReport:
    levels = get_cached_levels(symbol, tf)
    if not levels:
        return TechReport(score=0.0, summary="Auto-levels pending. Limited TA.")

    support = levels.get("support", [])
    resistance = levels.get("resistance", [])
    mid = levels.get("mid")
    bias = 0.0
    if price is not None and mid is not None:
        bias = 0.6 if price > mid else -0.6
    if bias > 0:
        bias_label = "bull"
    elif bias < 0:
        bias_label = "bear"
    else:
        bias_label = "neutral"
    summary = (
        f"Levels S={support[:2]} R={resistance[:2]} Mid={mid}. "
        f"Bias {bias_label}."
    )
    return TechReport(score=bias, summary=summary)


def fundamental_agent(symbol: str) -> FundReport:
    summary = (
        "Macro stance neutral. No live feeds; assume balanced liquidity/" "risk-on/off mix."
    )
    return FundReport(score=0.0, summary=summary)


def decide(symbol: str, tf: str, price: Optional[float]) -> Decision:
    tech = technical_agent(symbol, tf, price)
    fund = fundamental_agent(symbol)
    total_score = tech.score + fund.score

    if total_score >= 0.7:
        action = "BUY"
        confidence = "Medium"
    elif total_score <= -0.7:
        action = "SELL"
        confidence = "Medium"
    else:
        action = "WAIT"
        confidence = "Low"

    levels = get_cached_levels(symbol, tf) or {}
    support = levels.get("support", [])
    resistance = levels.get("resistance", [])
    mid = levels.get("mid")

    entry = price or mid
    stop_loss = support[0] if support else None
    take_profit = resistance[0] if resistance else None
    invalidation = "Break below support" if action == "BUY" else "Break above resistance"

    return Decision(
        action=action,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
        invalidation=invalidation,
        tech=tech,
        fund=fund,
    )


def decision_to_dict(decision: Decision) -> Dict[str, Any]:
    return {
        "action": decision.action,
        "entry": decision.entry,
        "stop_loss": decision.stop_loss,
        "take_profit": decision.take_profit,
        "confidence": decision.confidence,
        "invalidation": decision.invalidation,
        "tech": {
            "score": decision.tech.score,
            "summary": decision.tech.summary,
        },
        "fund": {
            "score": decision.fund.score,
            "summary": decision.fund.summary,
        },
    }


def format_decision(symbol: str, tf: str, decision: Decision) -> str:
    return (
        f"*Decision*: {decision.action}\n"
        f"*Entry*: {decision.entry or 'n/a'}\n"
        f"*Stop*: {decision.stop_loss or 'n/a'}\n"
        f"*Target*: {decision.take_profit or 'n/a'}\n"
        f"*Confidence*: {decision.confidence}\n"
        f"*Invalidation*: {decision.invalidation}\n"
        f"*Timeframe*: {tf}\n"
    )


def format_signal_card(symbol: str, tf: str, decision: Decision, reason: str) -> str:
    return (
        f"🚨 *AI Futures Signal — Official*\n"
        f"*Symbol*: {symbol}\n"
        f"*Action*: {decision.action}\n"
        f"*Entry*: {decision.entry or 'n/a'}\n"
        f"*Stop*: {decision.stop_loss or 'n/a'}\n"
        f"*Target*: {decision.take_profit or 'n/a'}\n"
        f"*Confidence*: {decision.confidence}\n"
        f"*Invalidation*: {decision.invalidation}\n"
        f"*Trigger*: {reason}\n"
        f"*TF*: {tf}\n"
        f"*Tech*: {decision.tech.summary}\n"
        f"*Fund*: {decision.fund.summary}\n"
    )
