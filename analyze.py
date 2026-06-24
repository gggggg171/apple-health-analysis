#!/usr/bin/env python3
"""
Apple Health Analyzer — CLI 入口

从 Apple Health 导出数据中提取、分析和生成健康报告。

用法:
    python analyze.py /path/to/apple_health_export/
    python analyze.py /path/to/apple_health_export/ --target 72
    python analyze.py /path/to/apple_health_export/ --output report.txt
    python analyze.py /path/to/apple_health_export/ --days 30 --no-plan
"""

import argparse
import os
import shutil
import sys
import tempfile

# 确保 lib 可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.parser import find_health_xml, parse_health_data, extract_zip
from lib.metrics import analyze
from lib.report import generate_report, generate_training_plan_text
from lib.html_report import generate_html_report
from lib.watcher import watch_folder


def main():
    parser = argparse.ArgumentParser(
        description="Apple Health 数据分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze.py ~/Downloads/apple_health_export/
  python analyze.py ~/Downloads/apple_health_export/ --target 72
  python analyze.py ~/Downloads/apple_health_export/ --days 30 --output report.txt
        """,
    )
    parser.add_argument(
        "export_dir",
        help="Apple Health 导出目录或 zip 文件路径",
    )
    parser.add_argument(
        "--target", "-t",
        type=float,
        default=None,
        help="目标体重 (kg)，用于生成热量计划和训练建议",
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=90,
        help="分析最近 N 天的数据（默认 90）",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="报告输出文件路径（默认输出到终端）",
    )
    parser.add_argument(
        "--no-plan",
        action="store_true",
        help="不生成训练计划",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="简略模式（不包含每日明细）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式的分析结果",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="生成可视化 HTML 报告",
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="监控模式：持续监控目录，自动分析新文件",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="监控模式检查间隔（秒，默认 60）",
    )

    args = parser.parse_args()

    # ── 监控模式 ──
    if args.watch:
        watch_path = os.path.abspath(args.export_dir)
        if not os.path.isdir(watch_path):
            print(f"错误: 监控模式需要目录路径: {watch_path}", file=sys.stderr)
            sys.exit(1)
        watch_folder(watch_path, target=args.target, interval=args.interval)
        return

    # 验证输入
    input_path = args.export_dir
    temp_dir = None

    if not os.path.exists(input_path):
        print(f"错误: 路径不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 如果是 zip 文件，先解压
    if input_path.lower().endswith(".zip"):
        print("正在解压 zip 文件...", file=sys.stderr)
        temp_dir = tempfile.mkdtemp(prefix="apple_health_")
        export_dir = extract_zip(input_path, temp_dir)
        print(f"解压完成: {export_dir}", file=sys.stderr)
    elif os.path.isdir(input_path):
        export_dir = input_path
    else:
        print(f"错误: 请提供目录或 zip 文件: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 查找 XML 文件
    print("正在查找 Apple Health 数据文件...", file=sys.stderr)
    try:
        xml_path = find_health_xml(export_dir)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    file_size_mb = os.path.getsize(xml_path) / (1024 * 1024)
    print(f"找到: {os.path.basename(xml_path)} ({file_size_mb:.0f} MB)", file=sys.stderr)

    # 解析
    print("正在解析数据（大文件可能需要 15-30 秒）...", file=sys.stderr)

    def progress(count):
        print(f"  已处理 {count:,} 条记录...", end="\r", file=sys.stderr)

    parse_result = parse_health_data(xml_path, progress_callback=progress)
    print(f"\n解析完成: {parse_result.record_count:,} 条记录, "
          f"{parse_result.workout_count} 条运动记录 "
          f"({parse_result.parse_time_sec:.1f}秒)", file=sys.stderr)

    # 分析
    print("正在分析数据...", file=sys.stderr)
    result = analyze(
        user_profile=parse_result.user_profile,
        records=parse_result.records,
        workouts=parse_result.workouts,
        target_weight=args.target,
        days=args.days,
    )

    # 输出
    if args.json:
        import json
        output = _result_to_dict(result)
        report = json.dumps(output, ensure_ascii=False, indent=2)
    else:
        report = generate_report(result, detailed=not args.brief)

        if not args.no_plan:
            plan_text = generate_training_plan_text(result)
            report += "\n\n" + plan_text

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存到: {args.output}", file=sys.stderr)
    elif args.json:
        print(report)
    else:
        print("\n" + report)

    # 生成 HTML 可视化报告
    if args.html:
        html_path = args.output.replace(".txt", ".html") if args.output else "health_report.html"
        html_content = generate_html_report(result)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML 报告已保存到: {html_path}", file=sys.stderr)
        # 尝试自动打开
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(html_path))

    # 清理临时目录
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


def _result_to_dict(result) -> dict:
    """将分析结果转为 JSON 可序列化的字典"""
    wt = result.weight_trend
    ap = result.activity_profile
    ch = result.cardio_health
    sc = result.health_score
    cp = result.calorie_plan

    output = {
        "user_profile": {
            "sex": result.user_profile.biological_sex,
            "age": result.user_profile.age,
            "height_cm": result.user_profile.height_cm,
        },
        "health_score": {
            "total": sc.total,
            "bmi_score": sc.bmi_score,
            "activity_score": sc.activity_score,
            "cardio_score": sc.cardio_score,
            "consistency_score": sc.consistency_score,
            "details": sc.details,
        },
        "weight": {
            "current_kg": wt.current_kg,
            "bmi": wt.bmi,
            "bmi_category": wt.bmi_category,
            "total_change_kg": wt.total_change_kg,
            "recent_30d_change_kg": wt.recent_30d_change_kg,
            "monthly_averages": wt.monthly_averages,
        },
        "activity": {
            "total_workouts": ap.total_workouts,
            "workouts_by_type": ap.workouts_by_type,
            "avg_daily_steps": ap.avg_daily_steps,
            "avg_daily_active_energy": ap.avg_daily_active_energy,
            "avg_daily_exercise_min": ap.avg_daily_exercise_min,
            "recent_30d_workouts": ap.recent_30d_workouts,
        },
        "cardio": {
            "resting_hr": ch.resting_hr_current,
            "vo2max": ch.vo2max_current,
            "vo2max_category": ch.vo2max_category,
        },
    }

    if cp:
        output["calorie_plan"] = {
            "bmr": cp.bmr,
            "tdee": cp.tdee,
            "target_intake": cp.target_intake,
            "deficit": cp.deficit,
            "weekly_loss_kg": cp.weekly_loss_kg,
            "weeks_to_goal": cp.weeks_to_goal,
            "protein_g": cp.protein_g,
        }

    return output


if __name__ == "__main__":
    main()
