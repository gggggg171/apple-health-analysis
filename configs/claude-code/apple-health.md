# Apple Health Analysis

Analyze Apple Health export data: weight trends, workout patterns, cardio fitness, calorie planning, and personalized training plans.

## When to Activate

This skill activates when the user asks to:
- Analyze Apple Health data, iPhone health export, health XML
- Check weight trends, workout stats, VO2Max, resting heart rate
- Generate a health report, calorie plan, or training plan from health data
- Questions like "为什么体重上升了", "分析我的健康数据"

## Prerequisites

- Python 3.9+ (standard library only)
- Apple Health export data folder (contains `export.xml` or `导出.xml`)

## Usage

Run the analysis tool:

```bash
# Basic analysis
python analyze.py /path/to/apple_health_export/

# With weight target
python analyze.py /path/to/apple_health_export/ --target 72

# Last 30 days only
python analyze.py /path/to/apple_health_export/ --days 30

# Save to file
python analyze.py /path/to/apple_health_export/ --output report.txt

# JSON output
python analyze.py /path/to/apple_health_export/ --json
```

## After Running

1. Read the terminal output
2. Summarize key findings in natural language
3. If weight increased: explain glycogen/water retention, muscle gain, appetite changes
4. Provide specific, actionable advice (not generic tips)
5. If `--target` was used: walk through the training plan with the user

## Key Metrics Reference

| Metric | Good | Warning |
|--------|------|---------|
| Resting HR | < 60 bpm | > 75 bpm |
| VO2Max | > 40 mL/min/kg | < 35 |
| Daily steps | > 10,000 | < 5,000 |
| BMI | 18.5-24 | > 28 |

## Privacy

All analysis is local. Summarize data — do not echo raw values back.
