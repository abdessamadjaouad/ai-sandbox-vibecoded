"""
Agent Report Generator

Produces professional, standards-aligned evaluation reports in both
Markdown (human-readable) and JSON (machine-readable) formats.

Report structure:
  1. Executive Summary      — Status, judgment badge, global score
  2. KPI Dashboard          — All 7 categories with interpretations
  3. Step-by-Step Analysis  — Bottleneck identification
  4. Tool Usage Audit       — Allowlist compliance, tool accuracy
  5. Scoring & Judgment     — ISO/IEC 25010 mapping
  6. Recommendations        — Actionable improvements
  7. Risk Assessment        — Production readiness risks
  8. Standards Compliance   — Checklist
"""

import json
from typing import Any

from backend.app.models.agent_api_contract import (
    AgentEvaluationJudgment,
    AgentKPIReport,
    JudgmentLevel,
)

import structlog

logger = structlog.get_logger(__name__)


class AgentReportGenerator:
    """
    Generate Markdown + JSON evaluation reports.

    Usage:
        generator = AgentReportGenerator()
        report = generator.generate(kpi_report, judgment)
    """

    JUDGMENT_BADGES = {
        JudgmentLevel.EXCELLENT: "✅ EXCELLENT",
        JudgmentLevel.ACCEPTABLE: "🟡 ACCEPTABLE",
        JudgmentLevel.MARGINAL: "🟠 MARGINAL",
        JudgmentLevel.FAIL: "🔴 FAIL",
    }

    def generate(
        self,
        kpi_report: AgentKPIReport,
        judgment: AgentEvaluationJudgment,
    ) -> dict[str, Any]:
        """
        Generate both Markdown and JSON reports.

        Returns:
            dict with "markdown" and "json" keys
        """
        markdown = self._generate_markdown(kpi_report, judgment)
        json_report = self._generate_json(kpi_report, judgment)

        logger.info(
            "agent_report_generated",
            evaluation_id=kpi_report.evaluation_id,
            judgment=judgment.judgment.value,
        )

        return {
            "markdown": markdown,
            "json": json_report,
        }

    # ------------------------------------------------------------------
    # Markdown generation
    # ------------------------------------------------------------------

    def _generate_markdown(
        self,
        report: AgentKPIReport,
        judgment: AgentEvaluationJudgment,
    ) -> str:
        lines: list[str] = []
        badge = self.JUDGMENT_BADGES[judgment.judgment]

        lines.append("# Agent Evaluation Report")
        lines.append("")
        lines.append(f"**Evaluation ID:** `{report.evaluation_id}`  ")
        lines.append(f"**Evaluated At:** {report.evaluated_at.isoformat()}Z  ")
        if report.agent_id:
            lines.append(f"**Agent ID:** `{report.agent_id}`  ")
        if report.workflow_id:
            lines.append(f"**Workflow ID:** `{report.workflow_id}`  ")
        lines.append(f"**Total Runs:** {report.run_count}")
        lines.append("")

        # Executive Summary
        lines.append("---")
        lines.append("")
        lines.append("## 1. Executive Summary")
        lines.append("")
        lines.append(f"### Judgment: {badge}")
        lines.append("")
        lines.append(f"- **Global Score:** {judgment.global_score:.1f} / 100")
        lines.append(f"- **Confidence:** {judgment.confidence:.1%}")
        lines.append(f"- **Success Rate:** {report.overview.success_rate:.2%} ({report.overview.success_count}/{report.overview.total_runs})")
        lines.append("")
        lines.append(f"> **Recommendation:** {judgment.recommendation}")
        lines.append("")

        # KPI Dashboard
        lines.append("---")
        lines.append("")
        lines.append("## 2. KPI Dashboard")
        lines.append("")

        # Overview
        lines.append("### 2.1 Overview")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Runs | {report.overview.total_runs} |")
        lines.append(f"| Successful | {report.overview.success_count} |")
        lines.append(f"| Failed | {report.overview.error_count} |")
        lines.append(f"| Partial | {report.overview.partial_count} |")
        lines.append(f"| Success Rate | {report.overview.success_rate:.2%} |")
        lines.append("")

        # Performance
        lines.append("### 2.2 Performance (ISO/IEC 25010 §8.1)")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Avg Latency | {report.performance.avg_latency_ms:.1f} ms |")
        lines.append(f"| Min Latency | {report.performance.min_latency_ms:.1f} ms |")
        lines.append(f"| Max Latency | {report.performance.max_latency_ms:.1f} ms |")
        lines.append(f"| P50 Latency | {report.performance.p50_latency_ms:.1f} ms |")
        lines.append(f"| P95 Latency | {report.performance.p95_latency_ms:.1f} ms |")
        lines.append(f"| P99 Latency | {report.performance.p99_latency_ms:.1f} ms |")
        lines.append(f"| Std Dev | {report.performance.std_latency_ms:.1f} ms |")
        lines.append("")

        # Reliability
        lines.append("### 2.3 Reliability (ISO/IEC 25010 §8.6)")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Success Rate | {report.reliability.success_rate:.2%} |")
        lines.append(f"| Error Rate | {report.reliability.error_rate:.2%} |")
        lines.append(f"| Retry Rate | {report.reliability.retry_rate:.2%} |")
        if report.reliability.mean_time_between_failures_ms:
            lines.append(f"| MTBF | {report.reliability.mean_time_between_failures_ms:.1f} ms |")
        if report.reliability.failure_types:
            lines.append(f"| Failure Types | {json.dumps(report.reliability.failure_types)} |")
        lines.append("")

        # Cost
        lines.append("### 2.4 Cost Efficiency (MLCommons)")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Cost | ${report.cost.total_cost_usd:.6f} |")
        lines.append(f"| Avg Cost/Run | ${report.cost.avg_cost_per_run_usd:.6f} |")
        lines.append(f"| Cost/Success | ${report.cost.cost_per_success_usd:.6f} |")
        if report.cost.cost_per_token_usd:
            lines.append(f"| Cost/Token | ${report.cost.cost_per_token_usd:.8f} |")
        lines.append("")

        # AI Usage
        lines.append("### 2.5 AI Usage")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Prompt Tokens | {report.ai_usage.total_prompt_tokens:,} |")
        lines.append(f"| Total Completion Tokens | {report.ai_usage.total_completion_tokens:,} |")
        lines.append(f"| Total Tokens | {report.ai_usage.total_tokens:,} |")
        lines.append(f"| Avg Prompt/Run | {report.ai_usage.avg_prompt_tokens_per_run:.1f} |")
        lines.append(f"| Avg Completion/Run | {report.ai_usage.avg_completion_tokens_per_run:.1f} |")
        lines.append(f"| Avg Tokens/Run | {report.ai_usage.avg_tokens_per_run:.1f} |")
        lines.append("")

        # Technical
        lines.append("### 2.6 Technical Metrics")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        if report.technical.avg_cpu_time_ms:
            lines.append(f"| Avg CPU Time | {report.technical.avg_cpu_time_ms:.1f} ms |")
        if report.technical.avg_memory_mb:
            lines.append(f"| Avg Memory | {report.technical.avg_memory_mb:.1f} MB |")
        lines.append(f"| Avg Network Calls | {report.technical.avg_network_calls:.1f} |")
        lines.append(f"| Total Retries | {report.technical.total_retries} |")
        lines.append("")

        # Step-by-Step Analysis
        lines.append("---")
        lines.append("")
        lines.append("## 3. Step-by-Step Analysis")
        lines.append("")
        if report.breakdowns.steps:
            lines.append("| Step | Avg (ms) | P95 (ms) | Min (ms) | Max (ms) | Instability | Success | Count |")
            lines.append("|------|----------|----------|----------|----------|-------------|---------|-------|")
            for step in report.breakdowns.steps:
                lines.append(
                    f"| {step.step_name} | {step.avg_latency_ms:.0f} | {step.p95_latency_ms:.0f} | "
                    f"{step.min_latency_ms:.0f} | {step.max_latency_ms:.0f} | {step.instability_ms:.0f} | "
                    f"{step.success_rate:.0%} | {step.occurrence_count} |"
                )
        else:
            lines.append("*No step-level data available.*")
        lines.append("")

        # Tool Usage Audit
        lines.append("---")
        lines.append("")
        lines.append("## 4. Tool Usage Audit")
        lines.append("")
        if report.breakdowns.tools:
            lines.append("| Tool | Avg (ms) | Max (ms) | Usage | Failure Rate | Success Rate |")
            lines.append("|------|----------|----------|-------|--------------|--------------|")
            for tool in report.breakdowns.tools:
                lines.append(
                    f"| {tool.tool_name} | {tool.avg_latency_ms:.0f} | {tool.max_latency_ms:.0f} | "
                    f"{tool.usage_count} | {tool.failure_rate:.1%} | {tool.success_rate:.1%} |"
                )
        else:
            lines.append("*No tool invocation data available.*")
        lines.append("")

        # Scoring & Judgment
        lines.append("---")
        lines.append("")
        lines.append("## 5. Scoring & Judgment")
        lines.append("")
        lines.append("### Category Breakdown")
        lines.append("")
        lines.append("| Category | Score | Weight | Weighted | Standard Reference |")
        lines.append("|----------|-------|--------|----------|--------------------|")
        for cs in judgment.category_scores:
            lines.append(
                f"| {cs.category} | {cs.score:.1f} | {cs.weight:.0%} | {cs.weighted_score:.1f} | {cs.standard_reference} |"
            )
        lines.append("")
        lines.append(f"**Global Score:** {judgment.global_score:.1f} / 100")
        lines.append("")

        # Recommendations
        lines.append("---")
        lines.append("")
        lines.append("## 6. Recommendations")
        lines.append("")
        lines.append(judgment.recommendation)
        lines.append("")
        if judgment.blocking_violations:
            lines.append("### Blocking Violations")
            lines.append("")
            for v in judgment.blocking_violations:
                lines.append(f"- ⚠️ {v}")
            lines.append("")

        # Risk Assessment
        lines.append("---")
        lines.append("")
        lines.append("## 7. Risk Assessment")
        lines.append("")
        lines.append(judgment.risk_assessment)
        lines.append("")

        # Standards Compliance
        lines.append("---")
        lines.append("")
        lines.append("## 8. Standards Compliance Checklist")
        lines.append("")
        lines.append("| Standard / Clause | Compliant |")
        lines.append("|-------------------|-----------|")
        for clause, compliant in judgment.standards_compliance.items():
            icon = "✅" if compliant else "❌"
            lines.append(f"| {clause} | {icon} |")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Report generated by AI Sandbox Agent Evaluation Layer*")
        lines.append("*Standards: ISO/IEC 25010:2023, IEEE 1012-2016, MLCommons AI Efficiency*")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # JSON generation
    # ------------------------------------------------------------------

    def _generate_json(
        self,
        report: AgentKPIReport,
        judgment: AgentEvaluationJudgment,
    ) -> dict[str, Any]:
        return {
            "evaluation_meta": {
                "evaluation_id": report.evaluation_id,
                "evaluated_at": report.evaluated_at.isoformat(),
                "agent_id": report.agent_id,
                "workflow_id": report.workflow_id,
                "run_count": report.run_count,
            },
            "kpi_report": report.model_dump(mode="json"),
            "judgment": judgment.model_dump(mode="json"),
        }
