"""
Apple Health XML 流式解析器

使用 iterparse 流式解析 1-2GB 的 Apple Health 导出 XML，
内存占用低，解析速度快。
"""

import os
import zipfile
import tempfile
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Apple Health Record 类型映射 ──────────────────────────────────

RECORD_TYPES = {
    # 体成分
    "HKQuantityTypeIdentifierBodyMass": "body_mass",
    "HKQuantityTypeIdentifierBodyMassIndex": "bmi",
    "HKQuantityTypeIdentifierHeight": "height",
    "HKQuantityTypeIdentifierBodyFatPercentage": "body_fat",
    "HKQuantityTypeIdentifierLeanBodyMass": "lean_mass",
    # 活动
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_energy",
    "HKQuantityTypeIdentifierAppleExerciseTime": "exercise_time",
    "HKQuantityTypeIdentifierAppleStandTime": "stand_time",
    "HKQuantityTypeIdentifierDistanceWalkingRunning": "distance",
    "HKQuantityTypeIdentifierFlightsClimbed": "flights",
    # 心血管
    "HKQuantityTypeIdentifierHeartRate": "heart_rate",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_hr",
    "HKQuantityTypeIdentifierWalkingHeartRateAverage": "walking_hr",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv",
    "HKQuantityTypeIdentifierVO2Max": "vo2max",
    "HKQuantityTypeIdentifierBloodPressureSystolic": "bp_systolic",
    "HKQuantityTypeIdentifierBloodPressureDiastolic": "bp_diastolic",
    # 睡眠
    "HKCategoryTypeIdentifierSleepAnalysis": "sleep",
    # 营养
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": "dietary_energy",
    "HKQuantityTypeIdentifierDietaryProtein": "dietary_protein",
    "HKQuantityTypeIdentifierDietaryCarbohydrates": "dietary_carbs",
    "HKQuantityTypeIdentifierDietaryFatTotal": "dietary_fat",
    # 其他
    "HKQuantityTypeIdentifierRespiratoryRate": "respiratory_rate",
    "HKQuantityTypeIdentifierOxygenSaturation": "blood_oxygen",
}

# 运动类型映射（英文 → 中文）
WORKOUT_TYPES = {
    "HKWorkoutActivityTypeRunning": "跑步",
    "HKWorkoutActivityTypeWalking": "步行",
    "HKWorkoutActivityTypeCycling": "骑行",
    "HKWorkoutActivityTypeSwimming": "游泳",
    "HKWorkoutActivityTypeYoga": "瑜伽",
    "HKWorkoutActivityTypeFunctionalStrengthTraining": "功能力量训练",
    "HKWorkoutActivityTypeTraditionalStrengthTraining": "传统力量训练",
    "HKWorkoutActivityTypeHighIntensityIntervalTraining": "HIIT",
    "HKWorkoutActivityTypeDance": "舞蹈",
    "HKWorkoutActivityTypeElliptical": "椭圆机",
    "HKWorkoutActivityTypeRowing": "划船",
    "HKWorkoutActivityTypeStairClimbing": "爬楼梯",
    "HKWorkoutActivityTypeCoreTraining": "核心训练",
    "HKWorkoutActivityTypeFlexibility": "柔韧性",
    "HKWorkoutActivityTypeCooldown": "放松拉伸",
    "HKWorkoutActivityTypePilates": "普拉提",
    "HKWorkoutActivityTypeHiking": "徒步",
    "HKWorkoutActivityTypeTennis": "网球",
    "HKWorkoutActivityTypeBasketball": "篮球",
    "HKWorkoutActivityTypeSoccer": "足球",
    "HKWorkoutActivityTypeBadminton": "羽毛球",
    "HKWorkoutActivityTypeTableTennis": "乒乓球",
    "HKWorkoutActivityTypeCardioDance": "有氧舞蹈",
    "HKWorkoutActivityTypeOther": "其他",
}


# ── 数据结构 ──────────────────────────────────────────────────────

@dataclass
class UserProfile:
    """用户基本信息"""
    date_of_birth: Optional[str] = None
    biological_sex: Optional[str] = None
    height_cm: Optional[float] = None

    @property
    def age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        try:
            dob = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
            return (datetime.now() - dob).days // 365
        except ValueError:
            return None


@dataclass
class HealthRecord:
    """单条健康记录"""
    record_type: str          # 解析后的类型名（如 "body_mass"）
    value: float
    unit: str
    source_name: str
    start_date: str           # ISO 格式
    end_date: str
    creation_date: Optional[str] = None


@dataclass
class WorkoutRecord:
    """运动记录"""
    activity_type: str        # 解析后的类型名（如 "跑步"）
    duration_min: float
    total_distance_km: Optional[float]
    total_energy_kcal: Optional[float]
    start_date: str
    end_date: str
    source_name: str = ""
    statistics: list = field(default_factory=list)


@dataclass
class ParseResult:
    """解析结果"""
    user_profile: UserProfile
    records: dict             # {type_name: [HealthRecord, ...]}
    workouts: list            # [WorkoutRecord, ...]
    record_count: int
    workout_count: int
    parse_time_sec: float


# ── 解压与文件查找 ────────────────────────────────────────────────

def extract_zip(zip_path: str, extract_to: str = None) -> str:
    """
    解压 Apple Health 导出的 zip 文件。

    Args:
        zip_path: zip 文件路径
        extract_to: 解压目标目录（None = 临时目录）

    Returns:
        解压后的目录路径
    """
    if extract_to is None:
        extract_to = tempfile.mkdtemp(prefix="apple_health_")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

    # Apple Health 导出的 zip 通常解压后有一个 apple_health_export 子目录
    # 或者直接就是 export.xml
    subdirs = [
        d for d in os.listdir(extract_to)
        if os.path.isdir(os.path.join(extract_to, d))
    ]

    # 如果只有一个子目录，进入它
    if len(subdirs) == 1:
        return os.path.join(extract_to, subdirs[0])

    return extract_to


def find_health_xml(export_dir: str) -> str:
    """在导出目录中找到 Health XML 文件"""
    import os

    # 常见文件名
    candidates = [
        "export.xml",
        "导出.xml",
        "apple_health_export.xml",
    ]

    for name in candidates:
        path = os.path.join(export_dir, name)
        if os.path.isfile(path):
            return path

    # 回退：找最大的 .xml 文件
    xml_files = []
    for f in os.listdir(export_dir):
        if f.endswith(".xml") and not f.startswith("."):
            full = os.path.join(export_dir, f)
            xml_files.append((os.path.getsize(full), full))

    if xml_files:
        xml_files.sort(reverse=True)
        return xml_files[0][1]

    raise FileNotFoundError(
        f"在 {export_dir} 中未找到 Apple Health XML 文件。"
        f"请确认目录包含 export.xml 或类似文件。"
    )


def parse_health_data(
    xml_path: str,
    record_types: Optional[set] = None,
    progress_callback=None,
) -> ParseResult:
    """
    流式解析 Apple Health XML 文件。

    Args:
        xml_path: XML 文件路径
        record_types: 要解析的记录类型集合（None = 全部）
        progress_callback: 进度回调 fn(element_count)

    Returns:
        ParseResult 包含用户信息、记录和运动数据
    """
    import time

    start_time = time.time()

    # 确定要解析的类型
    if record_types is None:
        wanted_types = set(RECORD_TYPES.keys())
    else:
        wanted_types = set()
        for rt in record_types:
            # 支持传入原始类型名或解析后的短名
            if rt in RECORD_TYPES:
                wanted_types.add(rt)
            else:
                # 反向查找
                for full_name, short_name in RECORD_TYPES.items():
                    if short_name == rt:
                        wanted_types.add(full_name)
                        break

    user_profile = UserProfile()
    records = {}    # {type_name: [HealthRecord]}
    workouts = []
    total_count = 0

    for event, elem in ET.iterparse(xml_path, events=("start", "end")):
        total_count += 1

        # 进度回调（每 50 万元素一次）
        if progress_callback and total_count % 500_000 == 0:
            progress_callback(total_count)

        # ── 用户信息 ──
        if event == "start" and elem.tag == "Me":
            user_profile.date_of_birth = elem.attrib.get(
                "HKCharacteristicTypeIdentifierDateOfBirth"
            )
            sex = elem.attrib.get("HKCharacteristicTypeIdentifierBiologicalSex", "")
            sex_map = {
                "HKBiologicalSexMale": "男",
                "HKBiologicalSexFemale": "女",
            }
            user_profile.biological_sex = sex_map.get(sex, sex)

        # ── 健康记录 ──
        if event == "end" and elem.tag == "Record":
            rtype = elem.attrib.get("type", "")
            if rtype in wanted_types:
                try:
                    value = float(elem.attrib.get("value", 0))
                except (ValueError, TypeError):
                    elem.clear()
                    continue

                short_name = RECORD_TYPES[rtype]
                rec = HealthRecord(
                    record_type=short_name,
                    value=value,
                    unit=elem.attrib.get("unit", ""),
                    source_name=elem.attrib.get("sourceName", ""),
                    start_date=elem.attrib.get("startDate", ""),
                    end_date=elem.attrib.get("endDate", ""),
                    creation_date=elem.attrib.get("creationDate"),
                )

                if short_name not in records:
                    records[short_name] = []
                records[short_name].append(rec)
            elem.clear()

        # ── 身高（从 Me 中也可能有，但通常在 Record 里） ──
        if event == "end" and elem.tag == "Record":
            rtype = elem.attrib.get("type", "")
            if rtype == "HKQuantityTypeIdentifierHeight":
                try:
                    h = float(elem.attrib.get("value", 0))
                    # Apple Health 存储身高为米
                    if h < 3:  # 米
                        user_profile.height_cm = h * 100
                    else:  # 已经是厘米
                        user_profile.height_cm = h
                except (ValueError, TypeError):
                    pass

        # ── 运动记录 ──
        if event == "end" and elem.tag == "Workout":
            wtype_raw = elem.attrib.get("workoutActivityType", "")
            wtype = WORKOUT_TYPES.get(wtype_raw, wtype_raw)

            try:
                duration = float(elem.attrib.get("duration", 0) or 0)
            except (ValueError, TypeError):
                duration = 0

            dist = elem.attrib.get("totalDistance", "")
            energy = elem.attrib.get("totalEnergyBurned", "")

            # 解析运动统计（能量可能在 statistics 里而非属性里）
            stats = []
            for stat in elem.findall("WorkoutStatistics"):
                stats.append(dict(stat.attrib))

            # 如果属性里没有能量，从 WorkoutStatistics 中提取
            if not energy:
                for stat in stats:
                    if "EnergyBurned" in stat.get("type", ""):
                        energy = stat.get("sum", "")
                        if energy:
                            break

            workout = WorkoutRecord(
                activity_type=wtype,
                duration_min=duration,
                total_distance_km=float(dist) if dist else None,
                total_energy_kcal=float(energy) if energy else None,
                start_date=elem.attrib.get("startDate", ""),
                end_date=elem.attrib.get("endDate", ""),
                source_name=elem.attrib.get("sourceName", ""),
                statistics=stats,
            )
            workouts.append(workout)
            elem.clear()

    elapsed = time.time() - start_time

    # 从记录中提取最新身高
    if not user_profile.height_cm and "height" in records and records["height"]:
        h = records["height"][-1].value
        user_profile.height_cm = h * 100 if h < 3 else h

    return ParseResult(
        user_profile=user_profile,
        records=records,
        workouts=workouts,
        record_count=total_count,
        workout_count=len(workouts),
        parse_time_sec=elapsed,
    )
