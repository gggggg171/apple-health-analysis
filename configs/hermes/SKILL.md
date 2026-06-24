---
name: apple-health-analysis
description: Use when the user wants to analyze Apple Health export data — weight trends, workout stats, VO2Max, resting heart rate, calorie planning, or generate personalized training plans from iPhone health data.
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [health, fitness, apple-health, weight-loss, workout, analysis]
    related_skills: []
---

# Apple Health Analysis

Analyze Apple Health export data: weight trends, workout patterns, cardio fitness, calorie planning, and personalized training plans.

## When to Use

- User shares an Apple Health export folder (contains `export.xml` or `导出.xml`)
- User asks to analyze weight, steps, workouts, heart rate, VO2Max from iPhone data
- User wants a health report, calorie plan, or training plan based on health data
- User says "analyze my health data", "check my Apple Health", "为什么体重上升了"

## Prerequisites

- Python 3.9+ (standard library only, no pip install needed)
- Apple Health export data folder

## Workflow

### Step 1: Locate the Tool

The analysis script should be cloned from the repo or found at:
```
/path/to/apple-health-analysis/analyze.py
```

If not present, clone it:
```bash
git clone https://github.com/YOUR_USERNAME/apple-health-analysis.git /tmp/apple-health-analysis
```

### Step 2: Run Analysis

```bash
# Basic analysis
python /path/to/apple-health-analysis/analyze.py /path/to/apple_health_export/

# With weight target (generates calorie + training plan)
python /path/to/apple-health-analysis/analyze.py /path/to/apple_health_export/ --target 72

# Last 30 days only
python /path/to/apple-health-analysis/analyze.py /path/to/apple_health_export/ --days 30

# Save report to file
python /path/to/apple-health-analysis/analyze.py /path/to/apple_health_export/ --output report.txt

# JSON output for programmatic use
python /path/to/apple-health-analysis/analyze.py /path/to/apple_health_export/ --json
```

### Step 3: Interpret Results

After running the script, read the output and provide a natural language summary to the user. Focus on:

1. **Weight trend** — Is it going up, down, or stable? What's the 30-day change?
2. **Root cause analysis** — If weight increased despite exercise, explain possible causes (muscle gain + water retention, increased appetite, glycogen storage)
3. **Activity assessment** — Are they meeting WHO guidelines (150 min/week moderate)?
4. **Cardio fitness** — VO2Max trend, resting heart rate
5. **Actionable advice** — Specific calorie targets, training adjustments

### Step 4: Generate Training Plan (if requested)

Run with `--target` to get a personalized plan. Then explain:
- Why this specific plan suits their current fitness level
- How to progress week by week
- Common mistakes to avoid

## Key Data Points to Highlight

| Metric | Good Sign | Warning Sign |
|--------|-----------|--------------|
| Resting HR | < 60 bpm | > 75 bpm |
| VO2Max | > 40 (young adult) | < 35 |
| Daily steps | > 10,000 | < 5,000 |
| Exercise min | > 30/day | < 15/day |
| BMI | 18.5-24 | > 28 |

## Privacy

- All analysis runs locally, no data uploaded
- Do NOT echo back raw health data in responses — summarize only
- If generating a report file, remind the user where it's saved

## Pitfalls

1. **Large files**: Apple Health XML can be 1-2GB. The parser uses streaming (`iterparse`), so memory is fine but parsing takes 15-30 seconds.
2. **Multiple readings per day**: Weight may have multiple entries per day — the tool averages them.
3. **Weight fluctuations**: A 1-3 kg daily swing is normal (water, food, glycogen). Focus on weekly/monthly trends, not daily.
4. **Glycogen trap**: Starting exercise can cause 2-3 kg weight gain from glycogen + water storage. This is NOT fat gain.
5. **Chinese file names**: The export XML may be named `导出.xml` instead of `export.xml`. The tool handles both.
