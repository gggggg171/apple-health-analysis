# Apple Health Analysis

Analyze Apple Health export data: weight trends, workout patterns, cardio fitness, calorie planning, and personalized training plans.

## When to Activate

This skill activates when the user asks to:
- Analyze Apple Health data, iPhone health export, health XML
- Check weight trends, workout stats, VO2Max, resting heart rate
- Generate a health report, calorie plan, or training plan from health data

## Prerequisites

- Python 3.9+ (standard library only)
- Apple Health export data folder (contains `export.xml` or `导出.xml`)

## Usage

```bash
# Basic analysis
python analyze.py /path/to/apple_health_export/

# With weight target (generates calorie + training plan)
python analyze.py /path/to/apple_health_export/ --target 72

# Last 30 days only
python analyze.py /path/to/apple_health_export/ --days 30

# Save report to file
python analyze.py /path/to/apple_health_export/ --output report.txt

# JSON output for programmatic use
python analyze.py /path/to/apple_health_export/ --json
```

## After Running

1. Read the script output
2. Summarize key findings in natural language for the user
3. If weight increased: explain glycogen/water retention, muscle gain, appetite changes
4. Provide specific, actionable advice (not generic tips)
5. If `--target` was used: walk through the training plan

## Key Metrics

| Metric | Good | Warning |
|--------|------|---------|
| Resting HR | < 60 bpm | > 75 bpm |
| VO2Max | > 40 | < 35 |
| Steps/day | > 10,000 | < 5,000 |
| BMI | 18.5-24 | > 28 |

## Pitfalls

- XML files can be 1-2GB; parsing takes 15-30 seconds
- Weight fluctuates 1-3 kg daily (normal); focus on trends
- Starting exercise causes 2-3 kg glycogen + water gain (not fat)
- File may be named `导出.xml` (Chinese) — the tool handles both
