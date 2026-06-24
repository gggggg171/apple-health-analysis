"""
文件夹监控模块

监控指定文件夹，自动检测新的 Apple Health 导出文件并分析。
用于配合 iOS 快捷指令实现自动同步分析。
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


STATE_FILE = ".apple_health_watch_state.json"


def load_state(watch_dir: str) -> dict:
    """加载已处理文件的状态"""
    state_path = os.path.join(watch_dir, STATE_FILE)
    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            return json.load(f)
    return {"processed_files": {}, "last_run": None}


def save_state(watch_dir: str, state: dict):
    """保存状态"""
    state_path = os.path.join(watch_dir, STATE_FILE)
    state["last_run"] = datetime.now().isoformat()
    with open(state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def find_new_files(watch_dir: str, state: dict) -> list:
    """
    在监控目录中查找新的 Apple Health 导出文件。

    支持的格式：
    - .zip 文件（Apple Health 导出压缩包）
    - 包含 export.xml / 导出.xml 的目录
    """
    new_files = []
    processed = state.get("processed_files", {})

    for item in os.listdir(watch_dir):
        # 跳过隐藏文件和状态文件
        if item.startswith(".") or item == STATE_FILE:
            continue

        full_path = os.path.join(watch_dir, item)

        # 检查 zip 文件
        if item.lower().endswith(".zip"):
            mtime = os.path.getmtime(full_path)
            key = f"{item}:{mtime}"
            if key not in processed:
                new_files.append(("zip", full_path, key))

        # 检查目录
        elif os.path.isdir(full_path):
            # 看看目录里有没有 Apple Health XML
            has_xml = False
            for sub in os.listdir(full_path):
                if sub in ("export.xml", "导出.xml"):
                    has_xml = True
                    break
                # 检查子目录（apple_health_export/）
                sub_path = os.path.join(full_path, sub)
                if os.path.isdir(sub_path):
                    for f in os.listdir(sub_path):
                        if f in ("export.xml", "导出.xml"):
                            has_xml = True
                            break

            if has_xml:
                mtime = os.path.getmtime(full_path)
                key = f"{item}:{mtime}"
                if key not in processed:
                    new_files.append(("dir", full_path, key))

    return new_files


def run_analysis(file_path: str, file_type: str, target: float = None) -> str:
    """
    对单个文件运行分析，返回报告路径。

    Returns:
        生成的报告文件路径
    """
    from lib.parser import find_health_xml, parse_health_data, extract_zip
    from lib.metrics import analyze
    from lib.report import generate_report
    from lib.html_report import generate_html_report
    import tempfile
    import shutil

    temp_dir = None

    # 确定目录
    if file_type == "zip":
        print(f"  正在解压: {os.path.basename(file_path)}", file=sys.stderr)
        temp_dir = tempfile.mkdtemp(prefix="apple_health_")
        export_dir = extract_zip(file_path, temp_dir)
    else:
        export_dir = file_path

    # 查找 XML
    try:
        xml_path = find_health_xml(export_dir)
    except FileNotFoundError as e:
        print(f"  错误: {e}", file=sys.stderr)
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    # 解析
    print(f"  正在解析: {os.path.basename(xml_path)}", file=sys.stderr)
    parse_result = parse_health_data(xml_path)
    print(f"  解析完成: {parse_result.record_count:,} 条记录 ({parse_result.parse_time_sec:.1f}秒)", file=sys.stderr)

    # 分析
    result = analyze(
        user_profile=parse_result.user_profile,
        records=parse_result.records,
        workouts=parse_result.workouts,
        target_weight=target,
        days=90,
    )

    # 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 文本报告
    report_dir = os.path.join(os.path.dirname(file_path), "reports")
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(report_dir, f"health_report_{timestamp}.txt")
    report_text = generate_report(result)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # HTML 报告
    html_path = os.path.join(report_dir, f"health_report_{timestamp}.html")
    html_content = generate_html_report(result)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 最新报告软链接（方便快速访问）
    latest_html = os.path.join(report_dir, "latest.html")
    latest_txt = os.path.join(report_dir, "latest.txt")
    for link, target_file in [(latest_html, html_path), (latest_txt, report_path)]:
        if os.path.exists(link) or os.path.islink(link):
            os.remove(link)
        os.symlink(os.path.basename(target_file), link)

    print(f"  报告已生成:", file=sys.stderr)
    print(f"    文本: {report_path}", file=sys.stderr)
    print(f"    HTML: {html_path}", file=sys.stderr)

    # 清理临时目录
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

    return html_path


def watch_folder(watch_dir: str, target: float = None, interval: int = 60):
    """
    监控文件夹，自动分析新的 Apple Health 导出。

    Args:
        watch_dir: 监控目录路径
        target: 目标体重 (kg)
        interval: 检查间隔（秒），默认 60 秒
    """
    print(f"🔍 开始监控: {watch_dir}", file=sys.stderr)
    print(f"   检查间隔: {interval} 秒", file=sys.stderr)
    print(f"   支持格式: .zip 文件 或 包含 export.xml 的目录", file=sys.stderr)
    if target:
        print(f"   目标体重: {target} kg", file=sys.stderr)
    print(f"   按 Ctrl+C 停止", file=sys.stderr)
    print("", file=sys.stderr)

    state = load_state(watch_dir)

    while True:
        try:
            new_files = find_new_files(watch_dir, state)

            if new_files:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现 {len(new_files)} 个新文件", file=sys.stderr)

                for file_type, file_path, state_key in new_files:
                    print(f"\n  处理: {os.path.basename(file_path)} ({file_type})", file=sys.stderr)

                    try:
                        html_path = run_analysis(file_path, file_type, target)
                        state["processed_files"][state_key] = {
                            "path": file_path,
                            "analyzed_at": datetime.now().isoformat(),
                            "report": html_path,
                        }
                        save_state(watch_dir, state)
                        print(f"  ✅ 完成", file=sys.stderr)
                    except Exception as e:
                        print(f"  ❌ 错误: {e}", file=sys.stderr)
                        state["processed_files"][state_key] = {
                            "path": file_path,
                            "error": str(e),
                            "error_at": datetime.now().isoformat(),
                        }
                        save_state(watch_dir, state)

            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 无新文件，等待中...", file=sys.stderr, end="\r")

            time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n监控已停止", file=sys.stderr)
            break
        except Exception as e:
            print(f"\n错误: {e}", file=sys.stderr)
            time.sleep(interval)
