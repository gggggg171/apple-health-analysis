"""
可视化 HTML 报告生成器

生成自包含的 HTML 健康分析报告，使用 Chart.js 绘制图表。
"""

import json
from datetime import datetime

from .metrics import AnalysisResult


def generate_html_report(result: AnalysisResult) -> str:
    """生成完整的 HTML 可视化报告"""
    wt = result.weight_trend
    ap = result.activity_profile
    ch = result.cardio_health
    sc = result.health_score
    cp = result.calorie_plan
    p = result.user_profile

    # ── 准备图表数据 ──

    # 体重趋势（按月）
    weight_months = sorted(wt.monthly_averages.keys())[-12:]
    weight_values = [round(wt.monthly_averages[m], 1) for m in weight_months]

    # 近14天体重
    recent_dates = sorted(wt.daily_values.keys())[-14:]
    recent_weights = [round(wt.daily_values[d], 1) for d in recent_dates]

    # 运动类型分布
    workout_labels = list(ap.workouts_by_type.keys())[:8]
    workout_counts = [ap.workouts_by_type[k] for k in workout_labels]

    # 近30天每日步数
    daily_steps_labels = []
    daily_steps_values = []
    for s in result.daily_summaries[-30:]:
        daily_steps_labels.append(s.date[5:])  # MM-DD
        daily_steps_values.append(s.steps)

    # 近30天活动消耗
    daily_energy_values = [round(s.active_energy_kcal) for s in result.daily_summaries[-30:]]

    # 近30天运动时间
    daily_exercise_values = [round(s.exercise_min) for s in result.daily_summaries[-30:]]

    # 静息心率趋势
    rhr_labels = [d for d, _ in ch.resting_hr_trend[-30:]]
    rhr_values = [v for _, v in ch.resting_hr_trend[-30:]]

    # VO2Max 趋势
    vo2_labels = [d for d, _ in ch.vo2max_trend[-30:]]
    vo2_values = [round(v, 1) for _, v in ch.vo2max_trend[-30:]]

    # 每日明细表格
    daily_rows = ""
    for s in result.daily_summaries[-14:]:
        w = f"{s.weight_avg:.1f}" if s.weight_avg else "—"
        rhr = f"{s.resting_hr:.0f}" if s.resting_hr else "—"
        vo2 = f"{s.vo2max:.1f}" if s.vo2max else "—"
        types = ", ".join(s.workout_types[:3]) if s.workout_types else "—"
        daily_rows += f"""
        <tr>
            <td>{s.date}</td>
            <td>{w}</td>
            <td>{s.steps:,}</td>
            <td>{s.active_energy_kcal:,.0f}</td>
            <td>{s.exercise_min:.0f}</td>
            <td>{rhr}</td>
            <td>{vo2}</td>
            <td>{types}</td>
        </tr>"""

    # 训练计划
    from .training_plan import generate_plan
    plan = generate_plan(
        current_weight=wt.current_kg,
        goal_weight=cp.goal_weight_kg if cp else None,
        avg_daily_steps=ap.avg_daily_steps,
        avg_daily_exercise_min=ap.avg_daily_exercise_min,
        recent_workouts=ap.recent_30d_types,
        vo2max=ch.vo2max_current,
        resting_hr=ch.resting_hr_current,
    )

    plan_rows = ""
    for d in plan.days:
        plan_rows += f"""
        <tr>
            <td>{d.day}</td>
            <td>{d.activity}</td>
            <td>{d.duration_min}分钟</td>
            <td><span class="intensity intensity-{d.intensity}">{d.intensity}</span></td>
            <td>{d.notes}</td>
        </tr>"""

    meal_rows = ""
    for m in plan.meals:
        meal_rows += f"""
        <tr>
            <td>{m.meal}</td>
            <td>{m.suggestion}</td>
            <td>{m.approx_kcal} kcal</td>
        </tr>"""

    # 健康评分数据
    score_data = json.dumps([sc.bmi_score, sc.activity_score, sc.cardio_score, sc.consistency_score])

    # 运动类型颜色
    workout_colors = json.dumps([
        "#7dd3c0", "#a8d8a8", "#d4a574", "#c49b7a",
        "#8fb5a3", "#b8c9a3", "#d1b894", "#9ec5c5"
    ][:len(workout_labels)])

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apple Health 健康分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --bg: #1a1a2e;
            --card: #16213e;
            --card-border: #0f3460;
            --text: #e0e0e0;
            --text-muted: #8899aa;
            --accent: #4cc9f0;
            --accent2: #7dd3c0;
            --accent3: #f0a500;
            --accent4: #e74c3c;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            font-size: 2em;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            text-align: center;
            color: var(--text-muted);
            margin-bottom: 30px;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .card {{
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
        }}
        .card h2 {{
            font-size: 1.1em;
            color: var(--accent);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .stat-value {{
            font-size: 2.2em;
            font-weight: 700;
            color: var(--accent2);
        }}
        .stat-label {{ color: var(--text-muted); font-size: 0.9em; }}
        .stat-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .stat-row:last-child {{ border-bottom: none; }}
        .chart-card {{ grid-column: span 2; }}
        .full-width {{ grid-column: 1 / -1; }}
        .score-ring {{
            width: 120px; height: 120px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 2em; font-weight: 700; margin: 0 auto 15px;
            background: conic-gradient(var(--accent) 0deg, var(--accent2) {sc.total * 3.6}deg, rgba(255,255,255,0.1) {sc.total * 3.6}deg);
            position: relative;
        }}
        .score-ring::after {{
            content: ''; position: absolute;
            width: 90px; height: 90px; border-radius: 50%;
            background: var(--card);
        }}
        .score-ring span {{ position: relative; z-index: 1; }}
        table {{
            width: 100%; border-collapse: collapse;
            font-size: 0.9em;
        }}
        th {{
            text-align: left; padding: 10px 12px;
            background: rgba(255,255,255,0.05);
            color: var(--accent); font-weight: 600;
            border-bottom: 2px solid var(--card-border);
        }}
        td {{
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .intensity {{
            padding: 2px 10px; border-radius: 12px;
            font-size: 0.85em; font-weight: 600;
        }}
        .intensity-低 {{ background: rgba(46,204,113,0.2); color: #2ecc71; }}
        .intensity-中 {{ background: rgba(243,156,18,0.2); color: #f39c12; }}
        .intensity-高 {{ background: rgba(231,76,60,0.2); color: #e74c3c; }}
        .badge {{
            display: inline-block; padding: 4px 12px;
            border-radius: 20px; font-size: 0.85em; font-weight: 600;
        }}
        .badge-good {{ background: rgba(46,204,113,0.2); color: #2ecc71; }}
        .badge-warn {{ background: rgba(243,156,18,0.2); color: #f39c12; }}
        .badge-bad {{ background: rgba(231,76,60,0.2); color: #e74c3c; }}
        .notes li {{ padding: 6px 0; color: var(--text-muted); }}
        .notes li::marker {{ color: var(--accent); }}
        canvas {{ max-height: 300px; }}
        @media (max-width: 768px) {{
            .chart-card {{ grid-column: span 1; }}
            .grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>Apple Health 健康分析报告</h1>
    <p class="subtitle">
        {p.biological_sex or ''} · {p.age or '?'}岁 · {p.height_cm or '?'}cm ·
        分析周期: 最近 {result.analysis_period_days} 天 ·
        生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </p>

    <!-- 顶部卡片 -->
    <div class="grid">
        <div class="card" style="text-align:center;">
            <h2>📊 健康评分</h2>
            <div class="score-ring"><span>{sc.total}</span></div>
            <div style="font-size:0.85em;color:var(--text-muted);">
                BMI {sc.bmi_score}/25 · 活动 {sc.activity_score}/35<br>
                心肺 {sc.cardio_score}/25 · 一致性 {sc.consistency_score}/15
            </div>
        </div>
        <div class="card">
            <h2>⚖️ 体重</h2>
            <div class="stat-value">{wt.current_kg:.1f} kg</div>
            <div class="stat-label">BMI {wt.bmi:.1f} ({wt.bmi_category})</div>
            <div style="margin-top:12px;">
                <div class="stat-row">
                    <span>起始体重</span><span>{wt.first_record_kg:.1f} kg</span>
                </div>
                <div class="stat-row">
                    <span>总变化</span><span style="color:{'#2ecc71' if wt.total_change_kg < 0 else '#e74c3c'}">{wt.total_change_kg:+.1f} kg</span>
                </div>
                <div class="stat-row">
                    <span>近30天</span><span style="color:{'#2ecc71' if (wt.recent_30d_change_kg or 0) < 0 else '#e74c3c'}">{(wt.recent_30d_change_kg or 0):+.1f} kg</span>
                </div>
            </div>
        </div>
        <div class="card">
            <h2>🏃 运动概况</h2>
            <div class="stat-value">{ap.total_workouts}</div>
            <div class="stat-label">总运动次数 · {ap.total_duration_hr:.0f} 小时</div>
            <div style="margin-top:12px;">
                <div class="stat-row">
                    <span>日均步数</span><span>{ap.avg_daily_steps:,.0f}</span>
                </div>
                <div class="stat-row">
                    <span>日均消耗</span><span>{ap.avg_daily_active_energy:,.0f} kcal</span>
                </div>
                <div class="stat-row">
                    <span>日均运动</span><span>{ap.avg_daily_exercise_min:.0f} 分钟</span>
                </div>
            </div>
        </div>
        <div class="card">
            <h2>💓 心肺健康</h2>
            <div style="display:flex;gap:30px;margin-bottom:10px;">
                <div>
                    <div class="stat-value" style="font-size:1.8em;">{ch.resting_hr_current or '—'}</div>
                    <div class="stat-label">静息心率 (bpm)</div>
                </div>
                <div>
                    <div class="stat-value" style="font-size:1.8em;">{ch.vo2max_current or '—'}</div>
                    <div class="stat-label">VO2Max ({ch.vo2max_category or '—'})</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid">
        <div class="card chart-card">
            <h2>📈 月平均体重趋势</h2>
            <canvas id="weightChart"></canvas>
        </div>
        <div class="card chart-card">
            <h2>📅 近14天体重变化</h2>
            <canvas id="recentWeightChart"></canvas>
        </div>
        <div class="card">
            <h2>🏋️ 运动类型分布</h2>
            <canvas id="workoutChart"></canvas>
        </div>
        <div class="card">
            <h2>📊 健康评分雷达</h2>
            <canvas id="scoreChart"></canvas>
        </div>
        <div class="card chart-card">
            <h2>👟 近30天每日步数</h2>
            <canvas id="stepsChart"></canvas>
        </div>
        <div class="card chart-card">
            <h2>🔥 近30天活动消耗</h2>
            <canvas id="energyChart"></canvas>
        </div>
        {"<div class='card chart-card'><h2>💓 静息心率趋势</h2><canvas id='rhrChart'></canvas></div>" if rhr_values else ""}
        {"<div class='card chart-card'><h2>🫁 VO2Max 趋势</h2><canvas id='vo2Chart'></canvas></div>" if vo2_values else ""}
    </div>

    <!-- 热量计划 -->
    {"" if not cp else f'''
    <div class="grid">
        <div class="card full-width">
            <h2>🍽️ 热量与营养计划</h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;">
                <div>
                    <div class="stat-value" style="font-size:1.6em;">{cp.bmr:,.0f}</div>
                    <div class="stat-label">基础代谢 (BMR) kcal/天</div>
                </div>
                <div>
                    <div class="stat-value" style="font-size:1.6em;">{cp.tdee:,.0f}</div>
                    <div class="stat-label">每日总消耗 (TDEE) kcal/天</div>
                </div>
                <div>
                    <div class="stat-value" style="font-size:1.6em;">{cp.target_intake:,.0f}</div>
                    <div class="stat-label">目标摄入 kcal/天</div>
                </div>
                <div>
                    <div class="stat-value" style="font-size:1.6em;">{cp.weeks_to_goal}</div>
                    <div class="stat-label">预计达到目标 (周)</div>
                </div>
            </div>
        </div>
    </div>
    '''}

    <!-- 训练计划 -->
    <div class="grid">
        <div class="card full-width">
            <h2>🏋️ 周训练计划</h2>
            <table>
                <tr><th>星期</th><th>训练内容</th><th>时长</th><th>强度</th><th>备注</th></tr>
                {plan_rows}
            </table>
        </div>
        <div class="card full-width">
            <h2>🥗 每日饮食建议</h2>
            <table>
                <tr><th>餐次</th><th>建议</th><th>热量</th></tr>
                {meal_rows}
            </table>
        </div>
    </div>

    <!-- 注意事项 -->
    <div class="grid">
        <div class="card full-width">
            <h2>⚠️ 注意事项</h2>
            <ul class="notes">
                {"".join(f"<li>{n}</li>" for n in plan.notes)}
            </ul>
        </div>
    </div>

    <!-- 每日明细 -->
    <div class="grid">
        <div class="card full-width">
            <h2>📋 每日明细（最近14天）</h2>
            <div style="overflow-x:auto;">
                <table>
                    <tr>
                        <th>日期</th><th>体重</th><th>步数</th>
                        <th>消耗(kcal)</th><th>运动(分钟)</th>
                        <th>心率</th><th>VO2Max</th><th>运动类型</th>
                    </tr>
                    {daily_rows}
                </table>
            </div>
        </div>
    </div>
</div>

<script>
const chartDefaults = {{
    color: '#8899aa',
    borderColor: 'rgba(255,255,255,0.1)',
}};
Chart.defaults.color = chartDefaults.color;
Chart.defaults.borderColor = chartDefaults.borderColor;

// 月均体重
new Chart(document.getElementById('weightChart'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(weight_months)},
        datasets: [{{
            label: '体重 (kg)',
            data: {json.dumps(weight_values)},
            borderColor: '#4cc9f0',
            backgroundColor: 'rgba(76,201,240,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#4cc9f0',
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});

// 近14天体重
new Chart(document.getElementById('recentWeightChart'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(recent_dates)},
        datasets: [{{
            label: '体重 (kg)',
            data: {json.dumps(recent_weights)},
            borderColor: '#7dd3c0',
            backgroundColor: 'rgba(125,211,192,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});

// 运动类型
new Chart(document.getElementById('workoutChart'), {{
    type: 'doughnut',
    data: {{
        labels: {json.dumps(workout_labels)},
        datasets: [{{
            data: {json.dumps(workout_counts)},
            backgroundColor: {workout_colors},
            borderWidth: 0,
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 15 }} }} }} }}
}});

// 健康评分雷达
new Chart(document.getElementById('scoreChart'), {{
    type: 'radar',
    data: {{
        labels: ['BMI', '活动', '心肺', '一致性'],
        datasets: [{{
            label: '评分',
            data: {score_data},
            backgroundColor: 'rgba(76,201,240,0.2)',
            borderColor: '#4cc9f0',
            pointBackgroundColor: '#4cc9f0',
        }}]
    }},
    options: {{
        responsive: true,
        scales: {{ r: {{ beginAtZero: true, max: 25, ticks: {{ stepSize: 5 }} }} }},
        plugins: {{ legend: {{ display: false }} }}
    }}
}});

// 每日步数
new Chart(document.getElementById('stepsChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(daily_steps_labels)},
        datasets: [{{
            label: '步数',
            data: {json.dumps(daily_steps_values)},
            backgroundColor: 'rgba(125,211,192,0.6)',
            borderColor: '#7dd3c0',
            borderWidth: 1,
            borderRadius: 4,
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});

// 活动消耗
new Chart(document.getElementById('energyChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(daily_steps_labels)},
        datasets: [{{
            label: '消耗 (kcal)',
            data: {json.dumps(daily_energy_values)},
            backgroundColor: 'rgba(240,165,0,0.6)',
            borderColor: '#f0a500',
            borderWidth: 1,
            borderRadius: 4,
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});
</script>
{"" if not rhr_values else f'''
<script>
// 静息心率
new Chart(document.getElementById('rhrChart'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(rhr_labels)},
        datasets: [{{
            label: '静息心率 (bpm)',
            data: {json.dumps(rhr_values)},
            borderColor: '#e74c3c',
            backgroundColor: 'rgba(231,76,60,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});
</script>
'''}
{"" if not vo2_values else f'''
<script>
// VO2Max
new Chart(document.getElementById('vo2Chart'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(vo2_labels)},
        datasets: [{{
            label: 'VO2Max (mL/min/kg)',
            data: {json.dumps(vo2_values)},
            borderColor: '#2ecc71',
            backgroundColor: 'rgba(46,204,113,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
        }}]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
}});
</script>
'''}
</body>
</html>"""

    return html
