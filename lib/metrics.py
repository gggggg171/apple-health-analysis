"""
健康指标计算与分析

从解析结果中计算各种健康指标、趋势和评分。
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .parser import HealthRecord, WorkoutRecord, UserProfile


# ── 数据结构 ──────────────────────────────────────────────────────

@dataclass
class DailySummary:
    """单日汇总"""
    date: str
    weight_avg: Optional[float] = None
    steps: int = 0
    active_energy_kcal: float = 0
    exercise_min: float = 0
    distance_km: float = 0
    flights: int = 0
    resting_hr: Optional[float] = None
    vo2max: Optional[float] = None
    workout_count: int = 0
    workout_types: list = field(default_factory=list)


@dataclass
class WeightTrend:
    """体重趋势"""
    current_kg: float
    first_record_date: str
    first_record_kg: float
    total_change_kg: float
    recent_30d_change_kg: Optional[float] = None
    monthly_averages: dict = field(default_factory=dict)  # {YYYY-MM: avg_kg}
    daily_values: dict = field(default_factory=dict)      # {YYYY-MM-DD: avg_kg}
    bmi: Optional[float] = None
    bmi_category: str = ""


@dataclass
class ActivityProfile:
    """活动概况"""
    total_workouts: int
    workouts_by_type: dict         # {type: count}
    total_duration_hr: float
    total_energy_kcal: float
    avg_daily_steps: float
    avg_daily_active_energy: float
    avg_daily_exercise_min: float
    recent_30d_workouts: int
    recent_30d_types: dict


@dataclass
class CardioHealth:
    """心肺健康指标"""
    resting_hr_current: Optional[float] = None
    resting_hr_trend: list = field(default_factory=list)  # [(date, value)]
    vo2max_current: Optional[float] = None
    vo2max_trend: list = field(default_factory=list)
    vo2max_category: str = ""


@dataclass
class HealthScore:
    """综合健康评分 (0-100)"""
    total: int
    bmi_score: int = 0
    activity_score: int = 0
    cardio_score: int = 0
    consistency_score: int = 0
    details: dict = field(default_factory=dict)


@dataclass
class CaloriePlan:
    """热量计划"""
    bmr: float                  # 基础代谢率
    tdee: float                 # 每日总消耗
    target_intake: float        # 目标摄入
    deficit: float              # 热量缺口
    weekly_loss_kg: float       # 预期每周减重
    weeks_to_goal: int          # 达到目标周数
    protein_g: float            # 建议蛋白质摄入
    goal_weight_kg: float


@dataclass
class AnalysisResult:
    """完整分析结果"""
    user_profile: UserProfile
    weight_trend: WeightTrend
    activity_profile: ActivityProfile
    cardio_health: CardioHealth
    health_score: HealthScore
    calorie_plan: Optional[CaloriePlan]
    daily_summaries: list        # [DailySummary]
    analysis_period_days: int


# ── 辅助函数 ──────────────────────────────────────────────────────

def _parse_date(date_str: str) -> Optional[datetime]:
    """解析 Apple Health 日期格式"""
    if not date_str:
        return None
    try:
        # 处理 "2024-01-15 10:30:00 +0800" 格式
        clean = date_str.split(" +")[0].split(" -")[0]
        return datetime.strptime(clean[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, IndexError):
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _daily_aggregate(records: list, record_type: str) -> dict:
    """按日聚合记录值"""
    daily = defaultdict(list)
    for rec in records:
        if rec.record_type == record_type:
            date = rec.start_date[:10]
            daily[date].append(rec.value)
    return {d: sum(v) / len(v) for d, v in daily.items()}


def _daily_sum(records: list, record_type: str) -> dict:
    """按日求和"""
    daily = defaultdict(float)
    for rec in records:
        if rec.record_type == record_type:
            date = rec.start_date[:10]
            daily[date] += rec.value
    return dict(daily)


def _bmi_category(bmi: float) -> str:
    """BMI 分类"""
    if bmi < 18.5:
        return "偏瘦"
    elif bmi < 24:
        return "正常"
    elif bmi < 28:
        return "偏胖"
    else:
        return "肥胖"


def _vo2max_category(vo2: float, age: int, sex: str) -> str:
    """VO2Max 分类（男性标准，女性略调）"""
    # 简化的年龄分级标准
    if sex == "女":
        vo2 *= 1.1  # 女性标准略低，归一化比较

    if age < 30:
        if vo2 >= 52: return "优秀"
        if vo2 >= 45: return "良好"
        if vo2 >= 39: return "中等"
        if vo2 >= 35: return "偏低"
        return "低"
    elif age < 40:
        if vo2 >= 50: return "优秀"
        if vo2 >= 43: return "良好"
        if vo2 >= 37: return "中等"
        if vo2 >= 33: return "偏低"
        return "低"
    else:
        if vo2 >= 48: return "优秀"
        if vo2 >= 41: return "良好"
        if vo2 >= 35: return "中等"
        if vo2 >= 31: return "偏低"
        return "低"


# ── 主分析函数 ────────────────────────────────────────────────────

def analyze(
    user_profile: UserProfile,
    records: dict,
    workouts: list,
    target_weight: Optional[float] = None,
    days: int = 90,
) -> AnalysisResult:
    """
    执行完整的健康数据分析。

    Args:
        user_profile: 用户基本信息
        records: {type_name: [HealthRecord]}
        workouts: [WorkoutRecord]
        target_weight: 目标体重 (kg)
        days: 分析最近 N 天的数据

    Returns:
        AnalysisResult 完整分析结果
    """
    now = datetime.now()
    cutoff = now - timedelta(days=days)

    # ── 1. 体重趋势 ──
    weight_trend = _analyze_weight(records, user_profile, cutoff)

    # ── 2. 活动概况 ──
    activity_profile = _analyze_activity(records, workouts, cutoff)

    # ── 3. 心肺健康 ──
    cardio_health = _analyze_cardio(records, user_profile)

    # ── 4. 健康评分 ──
    health_score = _calculate_score(
        weight_trend, activity_profile, cardio_health, user_profile
    )

    # ── 5. 热量计划 ──
    calorie_plan = None
    if target_weight and weight_trend.current_kg:
        calorie_plan = _calculate_calorie_plan(
            user_profile, weight_trend.current_kg, target_weight,
            activity_profile.avg_daily_active_energy,
        )

    # ── 6. 每日汇总 ──
    daily_summaries = _build_daily_summaries(records, workouts, cutoff)

    return AnalysisResult(
        user_profile=user_profile,
        weight_trend=weight_trend,
        activity_profile=activity_profile,
        cardio_health=cardio_health,
        health_score=health_score,
        calorie_plan=calorie_plan,
        daily_summaries=daily_summaries,
        analysis_period_days=days,
    )


def _analyze_weight(records: dict, profile: UserProfile, cutoff) -> WeightTrend:
    """分析体重趋势"""
    weight_recs = records.get("body_mass", [])
    if not weight_recs:
        return WeightTrend(
            current_kg=0, first_record_date="", first_record_kg=0,
            total_change_kg=0,
        )

    # 按日聚合
    daily = defaultdict(list)
    for rec in weight_recs:
        daily[rec.start_date[:10]].append(rec.value)
    daily_avg = {d: sum(v) / len(v) for d, v in daily.items()}

    sorted_dates = sorted(daily_avg.keys())
    current = daily_avg[sorted_dates[-1]]
    first_date = sorted_dates[0]
    first_val = daily_avg[sorted_dates[0]]

    # 月均值
    monthly = defaultdict(list)
    for d, v in daily_avg.items():
        monthly[d[:7]].append(v)
    monthly_avg = {m: sum(v) / len(v) for m, v in monthly.items()}

    # 近30天变化
    cutoff_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_30 = {d: v for d, v in daily_avg.items() if d >= cutoff_30}
    change_30d = None
    if len(recent_30) >= 2:
        vals = sorted(recent_30.items())
        change_30d = vals[-1][1] - vals[0][1]

    # BMI
    bmi = None
    bmi_cat = ""
    if profile.height_cm and current:
        h_m = profile.height_cm / 100
        bmi = current / (h_m ** 2)
        bmi_cat = _bmi_category(bmi)

    return WeightTrend(
        current_kg=current,
        first_record_date=first_date,
        first_record_kg=first_val,
        total_change_kg=current - first_val,
        recent_30d_change_kg=change_30d,
        monthly_averages=monthly_avg,
        daily_values=daily_avg,
        bmi=bmi,
        bmi_category=bmi_cat,
    )


def _analyze_activity(records: dict, workouts: list, cutoff) -> ActivityProfile:
    """分析活动概况"""
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    # 步数
    steps_daily = _daily_sum(records.get("steps", []), "steps")
    recent_steps = {d: v for d, v in steps_daily.items() if d >= cutoff_str}
    avg_steps = sum(recent_steps.values()) / max(len(recent_steps), 1)

    # 活动能量
    energy_daily = _daily_sum(records.get("active_energy", []), "active_energy")
    recent_energy = {d: v for d, v in energy_daily.items() if d >= cutoff_str}
    avg_energy = sum(recent_energy.values()) / max(len(recent_energy), 1)

    # 运动时间
    ex_daily = _daily_sum(records.get("exercise_time", []), "exercise_time")
    recent_ex = {d: v for d, v in ex_daily.items() if d >= cutoff_str}
    avg_ex = sum(recent_ex.values()) / max(len(recent_ex), 1)

    # 运动记录
    type_count = defaultdict(int)
    type_duration = defaultdict(float)
    type_energy = defaultdict(float)
    for w in workouts:
        type_count[w.activity_type] += 1
        type_duration[w.activity_type] += w.duration_min
        if w.total_energy_kcal:
            type_energy[w.activity_type] += w.total_energy_kcal

    total_dur = sum(type_duration.values()) / 60
    total_energy = sum(type_energy.values())

    # 近30天运动
    cutoff_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_w = [w for w in workouts if w.start_date[:10] >= cutoff_30]
    recent_types = defaultdict(int)
    for w in recent_w:
        recent_types[w.activity_type] += 1

    return ActivityProfile(
        total_workouts=len(workouts),
        workouts_by_type=dict(sorted(type_count.items(), key=lambda x: -x[1])),
        total_duration_hr=total_dur,
        total_energy_kcal=total_energy,
        avg_daily_steps=avg_steps,
        avg_daily_active_energy=avg_energy,
        avg_daily_exercise_min=avg_ex,
        recent_30d_workouts=len(recent_w),
        recent_30d_types=dict(sorted(recent_types.items(), key=lambda x: -x[1])),
    )


def _analyze_cardio(records: dict, profile: UserProfile) -> CardioHealth:
    """分析心肺健康"""
    # 静息心率
    rhr_recs = records.get("resting_hr", [])
    rhr_trend = []
    rhr_current = None
    if rhr_recs:
        rhr_recs.sort(key=lambda r: r.start_date)
        rhr_trend = [(r.start_date[:10], r.value) for r in rhr_recs[-30:]]
        rhr_current = rhr_recs[-1].value

    # VO2Max
    vo2_recs = records.get("vo2max", [])
    vo2_trend = []
    vo2_current = None
    vo2_cat = ""
    if vo2_recs:
        vo2_recs.sort(key=lambda r: r.start_date)
        vo2_trend = [(r.start_date[:10], r.value) for r in vo2_recs[-30:]]
        vo2_current = vo2_recs[-1].value
        age = profile.age or 30
        sex = profile.biological_sex or "男"
        vo2_cat = _vo2max_category(vo2_current, age, sex)

    return CardioHealth(
        resting_hr_current=rhr_current,
        resting_hr_trend=rhr_trend,
        vo2max_current=vo2_current,
        vo2max_trend=vo2_trend,
        vo2max_category=vo2_cat,
    )


def _calculate_score(
    weight: WeightTrend,
    activity: ActivityProfile,
    cardio: CardioHealth,
    profile: UserProfile,
) -> HealthScore:
    """计算综合健康评分 (0-100)"""
    details = {}
    total = 0

    # BMI 评分 (25分)
    bmi_score = 0
    if weight.bmi:
        if 18.5 <= weight.bmi < 24:
            bmi_score = 25
        elif 24 <= weight.bmi < 28:
            bmi_score = 15
        elif weight.bmi < 18.5:
            bmi_score = 10
        else:
            bmi_score = 5
        details["bmi"] = f"BMI {weight.bmi:.1f} ({weight.bmi_category})"
    total += bmi_score

    # 活动评分 (35分)
    act_score = 0
    if activity.avg_daily_steps >= 10000:
        act_score += 15
        details["steps"] = f"日均 {activity.avg_daily_steps:,.0f} 步 (优秀)"
    elif activity.avg_daily_steps >= 7000:
        act_score += 10
        details["steps"] = f"日均 {activity.avg_daily_steps:,.0f} 步 (良好)"
    elif activity.avg_daily_steps >= 4000:
        act_score += 5
        details["steps"] = f"日均 {activity.avg_daily_steps:,.0f} 步 (偏低)"
    else:
        details["steps"] = f"日均 {activity.avg_daily_steps:,.0f} 步 (低)"

    if activity.avg_daily_exercise_min >= 30:
        act_score += 10
        details["exercise"] = f"日均运动 {activity.avg_daily_exercise_min:.0f} 分钟"
    elif activity.avg_daily_exercise_min >= 15:
        act_score += 5

    if activity.recent_30d_workouts >= 12:
        act_score += 10
        details["workouts"] = f"近30天 {activity.recent_30d_workouts} 次运动"
    elif activity.recent_30d_workouts >= 8:
        act_score += 5
    total += act_score

    # 心肺评分 (25分)
    cardio_score = 0
    if cardio.resting_hr_current:
        if cardio.resting_hr_current <= 60:
            cardio_score += 12
        elif cardio.resting_hr_current <= 70:
            cardio_score += 8
        elif cardio.resting_hr_current <= 80:
            cardio_score += 4
        details["resting_hr"] = f"静息心率 {cardio.resting_hr_current:.0f} bpm"

    if cardio.vo2max_current:
        if cardio.vo2max_category == "优秀":
            cardio_score += 13
        elif cardio.vo2max_category == "良好":
            cardio_score += 10
        elif cardio.vo2max_category == "中等":
            cardio_score += 7
        else:
            cardio_score += 3
        details["vo2max"] = f"VO2Max {cardio.vo2max_current:.1f} ({cardio.vo2max_category})"
    total += cardio_score

    # ── 一致性评分 (15分) ──
    # 基于运动天数占比和步数稳定性
    cons_score = 0
    # 使用最近30天运动次数评估一致性
    if activity.recent_30d_workouts >= 20:
        cons_score = 15
    elif activity.recent_30d_workouts >= 12:
        cons_score = 10
    elif activity.recent_30d_workouts >= 6:
        cons_score = 5
    else:
        cons_score = 3
    total += cons_score

    return HealthScore(
        total=min(total, 100),
        bmi_score=bmi_score,
        activity_score=act_score,
        cardio_score=cardio_score,
        consistency_score=cons_score,
        details=details,
    )


def _calculate_calorie_plan(
    profile: UserProfile,
    current_weight: float,
    target_weight: float,
    avg_active_energy: float,
) -> CaloriePlan:
    """计算热量计划"""
    height_cm = profile.height_cm or 175
    age = profile.age or 25
    is_male = profile.biological_sex == "男"

    # Mifflin-St Jeor 公式计算 BMR
    if is_male:
        bmr = 10 * current_weight + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * current_weight + 6.25 * height_cm - 5 * age - 161

    # TDEE = BMR × 活动系数 + 额外活动消耗
    # 用 Apple Health 的活动能量更准确
    if avg_active_energy > 0:
        # Apple Health 的 activeEnergy 不含 BMR，直接加
        tdee = bmr + avg_active_energy
    else:
        # 估算活动系数
        tdee = bmr * 1.55  # 中等活动量

    # 每天 500 kcal 缺口 → 每周减 ~0.45 kg
    deficit = 500
    target_intake = tdee - deficit
    weekly_loss = deficit * 7 / 7700  # 7700 kcal ≈ 1kg 脂肪

    weeks = 0
    if current_weight > target_weight and weekly_loss > 0:
        weeks = int((current_weight - target_weight) / weekly_loss) + 1

    # 蛋白质：1.6-2g/kg 目标体重
    protein = target_weight * 1.8

    return CaloriePlan(
        bmr=bmr,
        tdee=tdee,
        target_intake=target_intake,
        deficit=deficit,
        weekly_loss_kg=weekly_loss,
        weeks_to_goal=weeks,
        protein_g=protein,
        goal_weight_kg=target_weight,
    )


def _build_daily_summaries(records: dict, workouts: list, cutoff) -> list:
    """构建每日汇总"""
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    # 收集所有日期
    all_dates = set()
    for type_records in records.values():
        for rec in type_records:
            d = rec.start_date[:10]
            if d >= cutoff_str:
                all_dates.add(d)
    for w in workouts:
        d = w.start_date[:10]
        if d >= cutoff_str:
            all_dates.add(d)

    # 按日聚合
    summaries = {}
    for date in sorted(all_dates):
        summaries[date] = DailySummary(date=date)

    # 体重
    for rec in records.get("body_mass", []):
        d = rec.start_date[:10]
        if d in summaries:
            s = summaries[d]
            if s.weight_avg is None:
                s.weight_avg = rec.value
            else:
                s.weight_avg = (s.weight_avg + rec.value) / 2

    # 步数
    for rec in records.get("steps", []):
        d = rec.start_date[:10]
        if d in summaries:
            summaries[d].steps += int(rec.value)

    # 活动能量
    for rec in records.get("active_energy", []):
        d = rec.start_date[:10]
        if d in summaries:
            summaries[d].active_energy_kcal += rec.value

    # 运动时间
    for rec in records.get("exercise_time", []):
        d = rec.start_date[:10]
        if d in summaries:
            summaries[d].exercise_min += rec.value

    # 静息心率
    for rec in records.get("resting_hr", []):
        d = rec.start_date[:10]
        if d in summaries:
            summaries[d].resting_hr = rec.value

    # VO2Max
    for rec in records.get("vo2max", []):
        d = rec.start_date[:10]
        if d in summaries:
            summaries[d].vo2max = rec.value

    # 运动记录
    for w in workouts:
        d = w.start_date[:10]
        if d in summaries:
            summaries[d].workout_count += 1
            if w.activity_type not in summaries[d].workout_types:
                summaries[d].workout_types.append(w.activity_type)

    return [summaries[d] for d in sorted(summaries.keys())]
