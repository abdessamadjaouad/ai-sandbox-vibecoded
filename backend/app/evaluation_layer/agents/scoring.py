"""
Agent Scoring & Judgment Engine

Computes weighted global scores and production-readiness judgments
aligned with international standards:
- ISO/IEC 25010: Software product quality model
- IEEE 1012: Software Verification & Validation (V&V)

The scoring normalizes KPIs to [0, 100] and applies configurable weights.
Judgment thresholds are fixed per standards best practices.
"""

import math
from typing import Any

from backend.app.models.agent_api_contract import (
    AgentEvaluationJudgment,
    AgentKPIReport,
    CategoryScore,
    JudgmentLevel,
)

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Standards-aligned default configuration
# =============================================================================

DEFAULT_WEIGHTS = {
    "performance": 0.25,      # ISO/IEC 25010: Performance Efficiency
    "reliability": 0.25,      # ISO/IEC 25010: Reliability
    "cost_efficiency": 0.15,  # MLCommons AI Efficiency
    "ai_efficiency": 0.15,    # Token utilization & cost per token
    "technical_efficiency": 0.10,  # Resource consumption
    "operational_maturity": 0.10,  # Step/tool stability
}

# Fixed judgment thresholds aligned with IEEE 1012 V&V maturity levels
JUDGMENT_THRESHOLDS = {
    JudgmentLevel.EXCELLENT: 85.0,   # Surpasses production benchmarks
    JudgmentLevel.ACCEPTABLE: 70.0,  # Meets minimum production criteria
    JudgmentLevel.MARGINAL: 50.0,    # Requires remediation
    # FAIL: < 50
}

# Blocking constraints that auto-downgrade judgment
DEFAULT_CONSTRAINTS = {
    "max_p95_latency_ms": 5000.0,
    "min_success_rate": 0.80,
    "max_avg_cost_usd": 1.00,
    "max_error_rate": 0.20,
}


class AgentScoringEngine:
    """
    Compute global scores and production-readiness judgments.

    Usage:
        engine = AgentScoringEngine()
        judgment = engine.score(kpi_report)
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> None:
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self.constraints = constraints or dict(DEFAULT_CONSTRAINTS)
        self._validate_weights()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, report: AgentKPIReport) -> AgentEvaluationJudgment:
        """
        Compute scoring and judgment from a KPI report.

        Args:
            report: Computed AgentKPIReport

        Returns:
            AgentEvaluationJudgment with global score, verdict, and recommendations
        """
        category_scores = self._compute_category_scores(report)
        global_score = self._compute_global_score(category_scores)
        violations = self._check_constraints(report)
        judgment = self._determine_judgment(global_score, violations)
        recommendation = self._generate_recommendation(judgment, category_scores, violations)
        risk = self._generate_risk_assessment(judgment, violations)
        compliance = self._generate_standards_compliance(category_scores, violations)

        # Confidence: higher sample size → higher confidence, capped at 0.95
        confidence = min(0.50 + 0.05 * math.log1p(report.run_count), 0.95)

        logger.info(
            "agent_scored",
            evaluation_id=report.evaluation_id,
            global_score=global_score,
            judgment=judgment.value,
            violations=len(violations),
        )

        return AgentEvaluationJudgment(
            evaluation_id=report.evaluation_id,
            global_score=round(global_score, 2),
            judgment=judgment,
            confidence=round(confidence, 4),
            category_scores=category_scores,
            blocking_violations=violations,
            recommendation=recommendation,
            risk_assessment=risk,
            standards_compliance=compliance,
        )

    # ------------------------------------------------------------------
    # Category scoring
    # ------------------------------------------------------------------

    def _compute_category_scores(self, report: AgentKPIReport) -> list[CategoryScore]:
        scores: list[CategoryScore] = []

        # 1. Performance Efficiency (ISO/IEC 25010 §8.1)
        perf = report.performance
        perf_score = self._score_performance(perf)
        scores.append(CategoryScore(
            category="Performance Efficiency",
            score=round(perf_score, 2),
            weight=self.weights["performance"],
            weighted_score=round(perf_score * self.weights["performance"], 2),
            interpretation=self._interpret_performance(perf, perf_score),
            standard_reference="ISO/IEC 25010:2023 §8.1 — Time behaviour & Capacity",
        ))

        # 2. Reliability (ISO/IEC 25010 §8.6)
        rel = report.reliability
        rel_score = self._score_reliability(rel)
        scores.append(CategoryScore(
            category="Reliability",
            score=round(rel_score, 2),
            weight=self.weights["reliability"],
            weighted_score=round(rel_score * self.weights["reliability"], 2),
            interpretation=self._interpret_reliability(rel, rel_score),
            standard_reference="ISO/IEC 25010:2023 §8.6 — Maturity, Availability, Fault tolerance",
        ))

        # 3. Cost Efficiency (MLCommons AI Efficiency)
        cost = report.cost
        cost_score = self._score_cost_efficiency(cost, report.ai_usage)
        scores.append(CategoryScore(
            category="Cost Efficiency",
            score=round(cost_score, 2),
            weight=self.weights["cost_efficiency"],
            weighted_score=round(cost_score * self.weights["cost_efficiency"], 2),
            interpretation=self._interpret_cost(cost, cost_score),
            standard_reference="MLCommons AI Efficiency — Cost per inference benchmark",
        ))

        # 4. AI Efficiency (Token utilization)
        ai = report.ai_usage
        ai_score = self._score_ai_efficiency(ai)
        scores.append(CategoryScore(
            category="AI Efficiency",
            score=round(ai_score, 2),
            weight=self.weights["ai_efficiency"],
            weighted_score=round(ai_score * self.weights["ai_efficiency"], 2),
            interpretation=self._interpret_ai_efficiency(ai, ai_score),
            standard_reference="MLCommons AI Efficiency — Token throughput & utilization",
        ))

        # 5. Technical Efficiency (Resource consumption)
        tech = report.technical
        tech_score = self._score_technical_efficiency(tech)
        scores.append(CategoryScore(
            category="Technical Efficiency",
            score=round(tech_score, 2),
            weight=self.weights["technical_efficiency"],
            weighted_score=round(tech_score * self.weights["technical_efficiency"], 2),
            interpretation=self._interpret_technical(tech, tech_score),
            standard_reference="ISO/IEC 25010:2023 §8.1.3 — Resource utilization",
        ))

        # 6. Operational Maturity (Stability)
        op_score = self._score_operational_maturity(report)
        scores.append(CategoryScore(
            category="Operational Maturity",
            score=round(op_score, 2),
            weight=self.weights["operational_maturity"],
            weighted_score=round(op_score * self.weights["operational_maturity"], 2),
            interpretation=self._interpret_operational_maturity(report, op_score),
            standard_reference="IEEE 1012-2016 §7.3.2 — Operational readiness criteria",
        ))

        return scores

    # ------------------------------------------------------------------
    # Scoring heuristics (0-100)
    # ------------------------------------------------------------------

    def _score_performance(self, perf) -> float:
        """Score based on P95 latency (lower is better)."""
        p95 = perf.p95_latency_ms
        if p95 <= 500:
            return 100.0
        elif p95 <= 1000:
            return 90.0 - (p95 - 500) / 500 * 10
        elif p95 <= 3000:
            return 80.0 - (p95 - 1000) / 2000 * 30
        elif p95 <= 5000:
            return 50.0 - (p95 - 3000) / 2000 * 20
        else:
            return max(10.0, 30.0 - (p95 - 5000) / 5000 * 20)

    def _score_reliability(self, rel) -> float:
        """Score based on success rate and retry rate."""
        sr = rel.success_rate
        rr = rel.retry_rate
        base = sr * 100.0
        penalty = rr * 30.0  # Up to 30% penalty for retries
        return max(0.0, base - penalty)

    def _score_cost_efficiency(self, cost, ai_usage) -> float:
        """Score based on cost per success and cost per token."""
        cps = cost.cost_per_success_usd
        cpt = cost.cost_per_token_usd or 0.0

        # Benchmarks: <$0.001 per success = excellent, >$0.10 = poor
        if cps <= 0.001:
            score = 100.0
        elif cps <= 0.01:
            score = 90.0 - (cps - 0.001) / 0.009 * 20
        elif cps <= 0.10:
            score = 70.0 - (cps - 0.01) / 0.09 * 40
        else:
            score = max(10.0, 30.0 - (cps - 0.10) / 0.90 * 20)

        # Token cost penalty
        if cpt and cpt > 0.0001:
            score -= min(20.0, (cpt - 0.0001) / 0.001 * 20)

        return max(0.0, score)

    def _score_ai_efficiency(self, ai) -> float:
        """Score based on token efficiency (completion ratio)."""
        total = ai.total_tokens
        if total == 0:
            return 50.0
        prompt_ratio = ai.total_prompt_tokens / total
        # Ideal: balanced or slightly more completion than prompt (agent produces output)
        # Penalize excessive prompt tokens relative to completion
        if prompt_ratio <= 0.5:
            return 100.0 - prompt_ratio * 20
        elif prompt_ratio <= 0.7:
            return 90.0 - (prompt_ratio - 0.5) / 0.2 * 30
        else:
            return max(20.0, 60.0 - (prompt_ratio - 0.7) / 0.3 * 40)

    def _score_technical_efficiency(self, tech) -> float:
        """Score based on CPU and memory consumption."""
        score = 100.0
        if tech.avg_cpu_time_ms is not None:
            if tech.avg_cpu_time_ms > 1000:
                score -= min(40.0, (tech.avg_cpu_time_ms - 1000) / 1000 * 40)
        if tech.avg_memory_mb is not None:
            if tech.avg_memory_mb > 512:
                score -= min(30.0, (tech.avg_memory_mb - 512) / 512 * 30)
        if tech.avg_network_calls > 5:
            score -= min(20.0, (tech.avg_network_calls - 5) / 10 * 20)
        return max(20.0, score)

    def _score_operational_maturity(self, report: AgentKPIReport) -> float:
        """Score based on step/tool stability and efficiency."""
        adv = report.advanced
        score = 100.0

        if adv.most_unstable_step:
            instability = adv.most_unstable_step.instability_ms
            if instability > 500:
                score -= min(30.0, (instability - 500) / 1500 * 30)

        if adv.slowest_step:
            slow = adv.slowest_step.avg_latency_ms
            if slow > 2000:
                score -= min(25.0, (slow - 2000) / 3000 * 25)

        # Penalize high tool failure rate
        tool_failures = [t.failure_rate for t in report.breakdowns.tools]
        if tool_failures:
            avg_tf = sum(tool_failures) / len(tool_failures)
            score -= avg_tf * 40.0

        # Step efficiency bonus
        if adv.step_efficiency_ratio is not None:
            if adv.step_efficiency_ratio >= 0.9:
                score += 10.0
            elif adv.step_efficiency_ratio >= 0.7:
                score += 5.0

        return max(10.0, min(100.0, score))

    # ------------------------------------------------------------------
    # Global score & judgment
    # ------------------------------------------------------------------

    def _compute_global_score(self, category_scores: list[CategoryScore]) -> float:
        return sum(cs.weighted_score for cs in category_scores)

    def _check_constraints(self, report: AgentKPIReport) -> list[str]:
        violations: list[str] = []

        if report.performance.p95_latency_ms > self.constraints["max_p95_latency_ms"]:
            violations.append(
                f"P95 latency ({report.performance.p95_latency_ms:.0f}ms) exceeds "
                f"threshold ({self.constraints['max_p95_latency_ms']:.0f}ms)"
            )

        if report.reliability.success_rate < self.constraints["min_success_rate"]:
            violations.append(
                f"Success rate ({report.reliability.success_rate:.2%}) below "
                f"minimum ({self.constraints['min_success_rate']:.0%})"
            )

        if report.cost.avg_cost_per_run_usd > self.constraints["max_avg_cost_usd"]:
            violations.append(
                f"Average cost (${report.cost.avg_cost_per_run_usd:.4f}) exceeds "
                f"budget (${self.constraints['max_avg_cost_usd']:.2f})"
            )

        if report.reliability.error_rate > self.constraints["max_error_rate"]:
            violations.append(
                f"Error rate ({report.reliability.error_rate:.2%}) exceeds "
                f"maximum ({self.constraints['max_error_rate']:.0%})"
            )

        return violations

    def _determine_judgment(
        self,
        global_score: float,
        violations: list[str],
    ) -> JudgmentLevel:
        """
        Determine judgment level.

        Blocking violations auto-downgrade by one level.
        """
        if global_score >= JUDGMENT_THRESHOLDS[JudgmentLevel.EXCELLENT]:
            base = JudgmentLevel.EXCELLENT
        elif global_score >= JUDGMENT_THRESHOLDS[JudgmentLevel.ACCEPTABLE]:
            base = JudgmentLevel.ACCEPTABLE
        elif global_score >= JUDGMENT_THRESHOLDS[JudgmentLevel.MARGINAL]:
            base = JudgmentLevel.MARGINAL
        else:
            base = JudgmentLevel.FAIL

        # Auto-downgrade if blocking violations exist
        if violations:
            downgrade_map = {
                JudgmentLevel.EXCELLENT: JudgmentLevel.ACCEPTABLE,
                JudgmentLevel.ACCEPTABLE: JudgmentLevel.MARGINAL,
                JudgmentLevel.MARGINAL: JudgmentLevel.FAIL,
                JudgmentLevel.FAIL: JudgmentLevel.FAIL,
            }
            return downgrade_map[base]

        return base

    # ------------------------------------------------------------------
    # Interpretation & recommendations
    # ------------------------------------------------------------------

    def _interpret_performance(self, perf, score: float) -> str:
        if score >= 90:
            return f"Excellent time behaviour (P95={perf.p95_latency_ms:.0f}ms). Exceeds production benchmarks."
        elif score >= 70:
            return f"Acceptable performance (P95={perf.p95_latency_ms:.0f}ms). Meets typical SLA requirements."
        elif score >= 50:
            return f"Marginal performance (P95={perf.p95_latency_ms:.0f}ms). Latency may impact user experience."
        else:
            return f"Poor performance (P95={perf.p95_latency_ms:.0f}ms). Critical latency issues detected."

    def _interpret_reliability(self, rel, score: float) -> str:
        if score >= 90:
            return f"Highly reliable ({rel.success_rate:.1%} success). Mature fault handling."
        elif score >= 70:
            return f"Reliable ({rel.success_rate:.1%} success). Acceptable for controlled deployment."
        elif score >= 50:
            return f"Unreliable ({rel.success_rate:.1%} success). Retry rate={rel.retry_rate:.1%}. Needs hardening."
        else:
            return f"Unstable ({rel.success_rate:.1%} success). Unacceptable for production."

    def _interpret_cost(self, cost, score: float) -> str:
        if score >= 90:
            return f"Excellent cost efficiency (${cost.cost_per_success_usd:.4f}/success)."
        elif score >= 70:
            return f"Acceptable cost (${cost.cost_per_success_usd:.4f}/success). Within budget."
        elif score >= 50:
            return f"High cost (${cost.cost_per_success_usd:.4f}/success). Consider optimization."
        else:
            return f"Excessive cost (${cost.cost_per_success_usd:.4f}/success). Major cost concern."

    def _interpret_ai_efficiency(self, ai, score: float) -> str:
        prompt_pct = ai.total_prompt_tokens / max(ai.total_tokens, 1) * 100
        if score >= 90:
            return f"Optimal token utilization ({prompt_pct:.0f}% prompt). Efficient inference."
        elif score >= 70:
            return f"Good token balance ({prompt_pct:.0f}% prompt). Within normal range."
        elif score >= 50:
            return f"Token-heavy ({prompt_pct:.0f}% prompt). Consider prompt optimization."
        else:
            return f"Inefficient token usage ({prompt_pct:.0f}% prompt). Major optimization opportunity."

    def _interpret_technical(self, tech, score: float) -> str:
        if score >= 90:
            return "Lean resource consumption. Suitable for high-throughput deployment."
        elif score >= 70:
            return "Moderate resource usage. Acceptable for standard deployment."
        elif score >= 50:
            return "Resource-intensive. May require infrastructure scaling."
        else:
            return "Excessive resource consumption. Infrastructure risk."

    def _interpret_operational_maturity(self, report, score: float) -> str:
        adv = report.advanced
        unstable = adv.most_unstable_step.step_name if adv.most_unstable_step else "N/A"
        if score >= 90:
            return "Stable operational profile. Consistent step/tool behaviour."
        elif score >= 70:
            return f"Generally stable. Monitor {unstable} for variance."
        elif score >= 50:
            return f"Operational instability detected ({unstable}). Remediation recommended."
        else:
            return f"Critical operational instability ({unstable}). Unsuitable for production."

    def _generate_recommendation(
        self,
        judgment: JudgmentLevel,
        category_scores: list[CategoryScore],
        violations: list[str],
    ) -> str:
        lowest = min(category_scores, key=lambda c: c.score)

        if judgment == JudgmentLevel.EXCELLENT:
            return (
                f"The agent exceeds production benchmarks with a strong profile across all categories. "
                f"Even so, continue monitoring '{lowest.category}' (score={lowest.score:.0f}) to maintain excellence."
            )
        elif judgment == JudgmentLevel.ACCEPTABLE:
            rec = (
                f"The agent meets minimum production criteria. Prioritize improving "
                f"'{lowest.category}' (score={lowest.score:.0f}) before scaling deployment."
            )
            if violations:
                rec += f" Address blocking violations: {violations[0]}."
            return rec
        elif judgment == JudgmentLevel.MARGINAL:
            return (
                f"The agent requires remediation before production deployment. "
                f"Critical gap in '{lowest.category}' (score={lowest.score:.0f}). "
                f"Action plan: 1) Fix blocking violations, 2) Optimize '{lowest.category}', 3) Re-evaluate."
            )
        else:
            return (
                f"The agent is currently unsuitable for production. "
                f"Severe deficiency in '{lowest.category}' (score={lowest.score:.0f}). "
                f"Recommended: architectural review and targeted remediation before re-testing."
            )

    def _generate_risk_assessment(
        self,
        judgment: JudgmentLevel,
        violations: list[str],
    ) -> str:
        if judgment == JudgmentLevel.EXCELLENT:
            return "Low risk. Ready for production deployment with standard monitoring."
        elif judgment == JudgmentLevel.ACCEPTABLE:
            base = "Moderate risk. Suitable for controlled deployment (canary / A-B testing)."
            if violations:
                base += f" Monitor: {', '.join(v.split(' ')[0] for v in violations)}."
            return base
        elif judgment == JudgmentLevel.MARGINAL:
            return (
                "High risk. Deployment without remediation may result in SLA breaches, "
                "user dissatisfaction, or cost overruns."
            )
        else:
            return (
                "Critical risk. Production deployment strongly discouraged. "
                "Failure modes may cause cascading system issues."
            )

    def _generate_standards_compliance(
        self,
        category_scores: list[CategoryScore],
        violations: list[str],
    ) -> dict[str, bool]:
        """
        Map scores to ISO/IEC 25010 clause compliance.
        """
        perf = next((c for c in category_scores if c.category == "Performance Efficiency"), None)
        rel = next((c for c in category_scores if c.category == "Reliability"), None)
        tech = next((c for c in category_scores if c.category == "Technical Efficiency"), None)

        return {
            "ISO_25010_8_1_Time_Behaviour": perf is not None and perf.score >= 70,
            "ISO_25010_8_1_Resource_Utilization": tech is not None and tech.score >= 60,
            "ISO_25010_8_6_Maturity": rel is not None and rel.score >= 70,
            "ISO_25010_8_6_Availability": rel is not None and rel.score >= 80,
            "IEEE_1012_VV_Ready": len(violations) == 0,
            "MLCommons_Cost_Efficient": any(
                c.category == "Cost Efficiency" and c.score >= 60 for c in category_scores
            ),
        }

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
