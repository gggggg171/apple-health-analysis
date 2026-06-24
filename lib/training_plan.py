"""
个性化训练计划生成

根据用户当前运动水平、体重目标和健康指标，
生成每周训练计划和饮食建议。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DayPlan:
    """单日训练计划"""
    day: str                    # "周一", "周二", ...
    activity: str               # 训练内容
    duration_min: int           # 预计时长
    intensity: str              # "低", "中", "高"
    notes: str = ""             # 备注


@dataclass
class MealPlan:
    """饮食建议"""
    meal: str                   # "早餐", "午餐", "晚餐", "加餐"
    suggestion: str             # 建议内容
    approx_kcal: int            # 大约热量


@dataclass
class WeeklyPlan:
    """一周训练计划"""
    days: list                  # [DayPlan]
    meals: list                 # [MealPlan]
    weekly_target_kcal: int     # 周消耗目标
    notes: list                 # 总体注意事项


def generate_plan(
    current_weight: float,
    goal_weight: Optional[float] = None,
    avg_daily_steps: float = 0,
    avg_daily_exercise_min: float = 0,
    recent_workouts: Optional[dict] = None,
    vo2max: Optional[float] = None,
    resting_hr: Optional[float] = None,
) -> WeeklyPlan:
    """
    生成个性化周训练计划。

    根据当前运动水平自适应调整强度，避免过度训练。
    """
    if recent_workouts is None:
        recent_workouts = {}

    goal_weight = goal_weight or current_weight
    weight_to_lose = max(0, current_weight - goal_weight)

    # 判断运动水平
    if avg_daily_exercise_min >= 60 and avg_daily_steps >= 15000:
        fitness_level = "高"
    elif avg_daily_exercise_min >= 30 and avg_daily_steps >= 8000:
        fitness_level = "中"
    else:
        fitness_level = "低"

    # 判断是否有力量训练基础
    has_strength = any(
        k in recent_workouts
        for k in ["传统力量训练", "功能力量训练", "核心训练"]
    )

    # 判断是否有跑步基础
    has_running = "跑步" in recent_workouts

    # ── 生成训练日 ──
    days = []

    if fitness_level == "高":
        # 高水平：有氧 + 力量交替，周末长距离
        days = [
            DayPlan("周一", "中等配速跑步", 40, "中", "心率保持130-150bpm"),
            DayPlan("周二", "上肢力量训练", 45, "中",
                    "俯卧撑4×15、哑铃推举4×12、划船4×12、平板支撑3×60s"),
            DayPlan("周三", "快走或轻松跑", 45, "低", "恢复日，心率120-140bpm"),
            DayPlan("周四", "下肢力量训练", 45, "中",
                    "深蹲4×15、弓步蹲4×12、罗马尼亚硬拉4×12、臀桥4×15"),
            DayPlan("周五", "HIIT间歇跑", 30, "高", "冲刺200m + 慢跑200m × 8组"),
            DayPlan("周六", "中长跑", 50, "中", "配速5'30\"-6'00\"，保持匀速"),
            DayPlan("周日", "休息 / 轻度步行", 30, "低", "主动恢复"),
        ]
    elif fitness_level == "中":
        # 中等水平：隔天有氧，穿插力量
        days = [
            DayPlan("周一", "快走或慢跑", 35, "中", "心率120-145bpm"),
            DayPlan("周二", "全身力量训练", 35, "中",
                    "深蹲3×12、俯卧撑3×12、平板支撑3×45s、臀桥3×15"),
            DayPlan("周三", "步行", 40, "低", "恢复日，目标8000步"),
            DayPlan("周四", "慢跑", 30, "中", "不追求速度，保持能说话的配速"),
            DayPlan("周五", "核心训练", 25, "中",
                    "卷腹3×20、俄罗斯转体3×15、死虫3×12、侧平板3×30s"),
            DayPlan("周六", "中等距离跑或骑行", 40, "中", "选择喜欢的有氧运动"),
            DayPlan("周日", "休息", 0, "低", "充分休息"),
        ]
    else:
        # 初级：从步行开始，逐步建立习惯
        days = [
            DayPlan("周一", "快走", 30, "低", "保持比日常走路快的节奏"),
            DayPlan("周二", "基础力量", 20, "低",
                    "深蹲3×10、俯卧撑3×8（可跪姿）、平板支撑3×30s"),
            DayPlan("周三", "步行", 30, "低", "轻松走，目标6000步"),
            DayPlan("周四", "慢跑/快走交替", 25, "中", "跑3分钟走2分钟，循环5次"),
            DayPlan("周五", "休息", 0, "低", ""),
            DayPlan("周六", "长距离步行", 45, "低", "目标10000步"),
            DayPlan("周日", "休息 / 拉伸", 15, "低", "全身拉伸15分钟"),
        ]

    # ── 饮食建议 ──
    meals = [
        MealPlan("早餐", "鸡蛋2个 + 全麦面包1片 + 牛奶250ml", 400),
        MealPlan("午餐", "米饭150g + 瘦肉/鱼150g + 蔬菜不限量", 650),
        MealPlan("加餐", "水果1份 + 坚果一小把(15g)", 200),
        MealPlan("晚餐", "米饭100g + 鸡胸肉/鱼150g + 蔬菜", 550),
        MealPlan("运动后", "蛋白粉1勺 或 鸡蛋2个", 200),
    ]

    # ── 注意事项 ──
    notes = []
    if weight_to_lose > 0:
        notes.append(f"目标减重 {weight_to_lose:.1f} kg，建议每周减 0.5 kg，不急于求成")
    notes.append("每天饮水 2.5-3L")
    notes.append("蛋白质摄入 120-150g/天（约 1.6-2g/kg 体重）")
    notes.append("每周称重 1-2 次（早起排便后），不要每天称")
    if vo2max and vo2max < 40:
        notes.append("VO2Max 偏低，重点提升心肺，优先保证有氧运动")
    if resting_hr and resting_hr > 75:
        notes.append("静息心率偏高，注意休息质量，避免过度训练")

    total_kcal = sum(d.duration_min * 8 for d in days)  # 粗估

    return WeeklyPlan(
        days=days,
        meals=meals,
        weekly_target_kcal=total_kcal,
        notes=notes,
    )


def _format_plan_text(plan: WeeklyPlan) -> str:
    """格式化为文本"""
    lines = []
    lines.append("【周训练计划】")
    lines.append("")
    lines.append(f"  {'星期':<6} {'训练内容':<20} {'时长':>6} {'强度':<4} 备注")
    lines.append("  " + "-" * 60)
    for d in plan.days:
        lines.append(
            f"  {d.day:<6} {d.activity:<20} {d.duration_min:>4}分钟 {d.intensity:<4} {d.notes}"
        )

    lines.append("")
    lines.append("【每日饮食建议】")
    for m in plan.meals:
        lines.append(f"  {m.meal}: {m.suggestion} (~{m.approx_kcal} kcal)")
    total_kcal = sum(m.approx_kcal for m in plan.meals)
    lines.append(f"  合计: ~{total_kcal} kcal/天")

    if plan.notes:
        lines.append("")
        lines.append("【注意事项】")
        for note in plan.notes:
            lines.append(f"  - {note}")

    return "\n".join(lines)


# 给 WeeklyPlan 添加 format_text 方法
WeeklyPlan.format_text = lambda self: _format_plan_text(self)
