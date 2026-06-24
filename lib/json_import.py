"""
JSON 数据导入

支持从 iOS 快捷指令输出的 JSON 格式导入健康数据。
用于日常快速分析（不包含完整 XML 导出的所有字段）。
"""

import json
import os
from datetime import datetime, timedelta

from .parser import UserProfile, HealthRecord, WorkoutRecord, ParseResult


def find_json_files(directory: str) -> list:
    """在目录中查找健康数据 JSON 文件"""
    json_files = []
    for item in os.listdir(directory):
        if item.endswith(".json") and not item.startswith("."):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                json_files.append(full_path)
    return sorted(json_files)


def parse_json_health_data(json_path: str) -> ParseResult:
    """
    解析快捷指令导出的 JSON 健康数据。

    JSON 格式：
    {
        "export_date": "2026-06-24",
        "days": [
            {
                "date": "2026-06-24",
                "steps": 12345,
                "weight_kg": 75.5,
                "heart_rate_avg": 72,
                "resting_heart_rate": 59,
                "vo2max": 42.5,
                "exercise_minutes": 45,
                "active_energy_kcal": 800,
                "flights_climbed": 5,
                "distance_km": 8.5,
                "workouts": [
                    {
                        "type": "Running",
                        "duration_min": 30,
                        "kcal": 350,
                        "distance_km": 5.0
                    }
                ]
            }
        ]
    }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_profile = UserProfile()
    records = {}
    workouts = []

    days = data.get("days", [])

    for day in days:
        date = day.get("date", "")

        # 步数
        steps = day.get("steps")
        if steps is not None:
            rec = HealthRecord(
                record_type="steps",
                value=float(steps),
                unit="count",
                source_name="Shortcut",
                start_date=f"{date} 00:00:00 +0000",
                end_date=f"{date} 23:59:59 +0000",
            )
            records.setdefault("steps", []).append(rec)

        # 体重
        weight = day.get("weight_kg")
        if weight is not None:
            rec = HealthRecord(
                record_type="body_mass",
                value=float(weight),
                unit="kg",
                source_name="Shortcut",
                start_date=f"{date} 08:00:00 +0000",
                end_date=f"{date} 08:00:00 +0000",
            )
            records.setdefault("body_mass", []).append(rec)

        # 静息心率
        rhr = day.get("resting_heart_rate")
        if rhr is not None:
            rec = HealthRecord(
                record_type="resting_hr",
                value=float(rhr),
                unit="bpm",
                source_name="Shortcut",
                start_date=f"{date} 00:00:00 +0000",
                end_date=f"{date} 23:59:59 +0000",
            )
            records.setdefault("resting_hr", []).append(rec)

        # VO2Max
        vo2 = day.get("vo2max")
        if vo2 is not None:
            rec = HealthRecord(
                record_type="vo2max",
                value=float(vo2),
                unit="mL/min/kg",
                source_name="Shortcut",
                start_date=f"{date} 00:00:00 +0000",
                end_date=f"{date} 23:59:59 +0000",
            )
            records.setdefault("vo2max", []).append(rec)

        # 运动时间
        ex_min = day.get("exercise_minutes")
        if ex_min is not None:
            rec = HealthRecord(
                record_type="exercise_time",
                value=float(ex_min),
                unit="min",
                source_name="Shortcut",
                start_date=f"{date} 00:00:00 +0000",
                end_date=f"{date} 23:59:59 +0000",
            )
            records.setdefault("exercise_time", []).append(rec)

        # 活动能量
        energy = day.get("active_energy_kcal")
        if energy is not None:
            rec = HealthRecord(
                record_type="active_energy",
                value=float(energy),
                unit="kcal",
                source_name="Shortcut",
                start_date=f"{date} 00:00:00 +0000",
                end_date=f"{date} 23:59:59 +0000",
            )
            records.setdefault("active_energy", []).append(rec)

        # 运动记录
        for w in day.get("workouts", []):
            workout = WorkoutRecord(
                activity_type=w.get("type", "其他"),
                duration_min=float(w.get("duration_min", 0)),
                total_distance_km=w.get("distance_km"),
                total_energy_kcal=w.get("kcal"),
                start_date=f"{date} 12:00:00 +0000",
                end_date=f"{date} 12:00:00 +0000",
                source_name="Shortcut",
            )
            workouts.append(workout)

    total_records = sum(len(v) for v in records.values())

    return ParseResult(
        user_profile=user_profile,
        records=records,
        workouts=workouts,
        record_count=total_records,
        workout_count=len(workouts),
        parse_time_sec=0,
    )


def parse_multiple_json(directory: str) -> ParseResult:
    """
    合并目录中所有 JSON 文件的数据。

    用于处理快捷指令每天生成的独立 JSON 文件。
    """
    json_files = find_json_files(directory)
    if not json_files:
        raise FileNotFoundError(f"在 {directory} 中未找到 JSON 文件")

    merged_profile = UserProfile()
    merged_records = {}
    merged_workouts = []
    total_count = 0

    for jf in json_files:
        result = parse_json_health_data(jf)
        # 合并记录
        for rtype, recs in result.records.items():
            merged_records.setdefault(rtype, []).extend(recs)
        merged_workouts.extend(result.workouts)
        total_count += result.record_count

    return ParseResult(
        user_profile=merged_profile,
        records=merged_records,
        workouts=merged_workouts,
        record_count=total_count,
        workout_count=len(merged_workouts),
        parse_time_sec=0,
    )
