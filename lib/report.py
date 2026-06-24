"""
报告生成

将分析结果格式化为可读的文本报告。
"""

from datetime import datetime
from typing import Optional

from .metrics import AnalysisResult, CaloriePlan


def generate_report(result: AnalysisResult, detailed: bool = True) -> str:
    """
    生成完整的健康分析报告。

    Args:
        result: 分析结果
        detailed: 是否包含详细数据

    Returns:
        格式化的文本报告
    """
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("=" * 60)
    lines.append("  Apple Health 健康分析报告")
    lines.append(f"  生成时间: {now}")
    lines.append("=" * 60)

    # ── 基本信息 ──
    p = result.user_profile
    lines.append("")
    lines.append("【基本信息】")
    if p.biological_sex:
        lines.append(f"  性别: {p.biological_sex}")
    if p.age:
        lines.append(f"  年龄: {p.age} 岁")
    if p.height_cm:
        lines.append(f"  身高: {p.height_cm:.0f} cm")
    lines.append(f"  分析周期: 最近 {result.analysis_period_days} 天")

    # ── 健康评分 ──
    score = result.health_score
    lines.append("")
    lines.append("【综合健康评分】")
    lines.append(f"  总分: {score.total}/100")
    lines.append(f"    BMI 评分:       {score.bmi_score}/25")
    lines.append(f"    活动评分:       {score.activity_score}/35")
    lines.append(f"    心肺评分:       {score.cardio_score}/25")
    lines.append(f"    一致性评分:     {score.consistency_score}/15")
    if score.details:
        lines.append("  指标明细:")
        for key, val in score.details.items():
            lines.append(f"    - {val}")

    # ── 体重分析 ──
    wt = result.weight_trend
    lines.append("")
    lines.append("【体重分析】")
    if wt.current_kg:
        lines.append(f"  当前体重: {wt.current_kg:.1f} kg")
        lines.append(f"  起始体重: {wt.first_record_kg:.1f} kg ({wt.first_record_date})")
        lines.append(f"  总变化:   {wt.total_change_kg:+.1f} kg")
        if wt.bmi:
            lines.append(f"  BMI:      {wt.bmi:.1f} ({wt.bmi_category})")
        if wt.recent_30d_change_kg is not None:
            lines.append(f"  近30天:   {wt.recent_30d_change_kg:+.1f} kg")

        # 月均趋势
        if wt.monthly_averages:
            lines.append("")
            lines.append("  月平均体重:")
            for month, avg in sorted(wt.monthly_averages.items())[-12:]:
                bar = "█" * int((avg - 50) / 1)
                lines.append(f"    {month}: {avg:.1f} kg  {bar}")

        # 近14天趋势
        if detailed and wt.daily_values:
            lines.append("")
            lines.append("  最近14天体重:")
            recent = sorted(wt.daily_values.items())[-14:]
            for date, val in recent:
                lines.append(f"    {date}: {val:.1f} kg")
    else:
        lines.append("  未找到体重数据")

    # ── 活动分析 ──
    ap = result.activity_profile
    lines.append("")
    lines.append("【运动与活动】")
    lines.append(f"  总运动次数: {ap.total_workouts}")
    lines.append(f"  总运动时长: {ap.total_duration_hr:.1f} 小时")
    lines.append(f"  总消耗:     {ap.total_energy_kcal:,.0f} kcal")

    if ap.workouts_by_type:
        lines.append("")
        lines.append("  运动类型分布:")
        for wtype, count in ap.workouts_by_type.items():
            lines.append(f"    {wtype}: {count} 次")

    lines.append("")
    lines.append("  日均指标:")
    lines.append(f"    步数:     {ap.avg_daily_steps:,.0f} 步")
    lines.append(f"    活动消耗: {ap.avg_daily_active_energy:,.0f} kcal")
    lines.append(f"    运动时间: {ap.avg_daily_exercise_min:.0f} 分钟")

    if ap.recent_30d_types:
        lines.append("")
        lines.append(f"  近30天运动: {ap.recent_30d_workouts} 次")
        for wtype, count in ap.recent_30d_types.items():
            lines.append(f"    {wtype}: {count} 次")

    # ── 心肺健康 ──
    ch = result.cardio_health
    lines.append("")
    lines.append("【心肺健康】")
    if ch.resting_hr_current:
        lines.append(f"  静息心率: {ch.resting_hr_current:.0f} bpm")
    if ch.vo2max_current:
        lines.append(f"  VO2Max:   {ch.vo2max_current:.1f} mL/min/kg ({ch.vo2max_category})")

    if detailed and ch.resting_hr_trend:
        lines.append("")
        lines.append("  静息心率趋势 (最近10条):")
        for date, val in ch.resting_hr_trend[-10:]:
            lines.append(f"    {date}: {val:.0f} bpm")

    if detailed and ch.vo2max_trend:
        lines.append("")
        lines.append("  VO2Max 趋势 (最近10条):")
        for date, val in ch.vo2max_trend[-10:]:
            lines.append(f"    {date}: {val:.1f} mL/min/kg")

    # ── 热量计划 ──
    cp = result.calorie_plan
    if cp:
        lines.append("")
        lines.append("【热量与营养计划】")
        lines.append(f"  基础代谢 (BMR): {cp.bmr:,.0f} kcal/天")
        lines.append(f"  每日总消耗 (TDEE): {cp.tdee:,.0f} kcal/天")
        lines.append(f"  目标摄入: {cp.target_intake:,.0f} kcal/天")
        lines.append(f"  每日缺口: {cp.deficit} kcal")
        lines.append(f"  预期每周减重: {cp.weekly_loss_kg:.2f} kg")
        lines.append(f"  达到目标预计: {cp.weeks_to_goal} 周")
        lines.append(f"  建议蛋白质: {cp.protein_g:.0f} g/天")

    # ── 每日明细（最近7天）──
    if detailed and result.daily_summaries:
        lines.append("")
        lines.append("【每日明细（最近7天）】")
        lines.append(f"  {'日期':<12} {'体重':>6} {'步数':>8} {'消耗':>8} {'运动':>6} {'心率':>5}")
        lines.append("  " + "-" * 52)
        for s in result.daily_summaries[-7:]:
            w = f"{s.weight_avg:.1f}" if s.weight_avg else "—"
            rhr = f"{s.resting_hr:.0f}" if s.resting_hr else "—"
            lines.append(
                f"  {s.date:<12} {w:>5}kg {s.steps:>7,} {s.active_energy_kcal:>7.0f} "
                f"{s.exercise_min:>5.0f}' {rhr:>4}"
            )

    lines.append("")
    lines.append("=" * 60)
    lines.append("  报告结束")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_training_plan_text(result: AnalysisResult) -> str:
    """生成训练计划文本（调用 training_plan 模块）"""
    from .training_plan import generate_plan

    plan = generate_plan(
        current_weight=result.weight_trend.current_kg,
        goal_weight=result.calorie_plan.goal_weight_kg if result.calorie_plan else None,
        avg_daily_steps=result.activity_profile.avg_daily_steps,
        avg_daily_exercise_min=result.activity_profile.avg_daily_exercise_min,
        recent_workouts=result.activity_profile.recent_30d_types,
        vo2max=result.cardio_health.vo2max_current,
        resting_hr=result.cardio_health.resting_hr_current,
    )

    return plan.format_text()
