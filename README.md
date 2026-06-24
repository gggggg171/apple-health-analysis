# Apple Health Analyzer

从 Apple Health 导出数据中提取、分析和可视化你的健康趋势。支持体重追踪、运动分析、心肺功能评估，并生成个性化训练计划。

## 功能

- **体重趋势分析**：月均值、日均值、波动范围，区分真实增重与水分波动
- **运动记录统计**：自动识别运动类型，按类型/时间维度汇总
- **心肺功能评估**：静息心率、VO2Max 趋势追踪
- **活动能量消耗**：日/周/月活动消耗分析
- **TDEE 估算**：基于 BMR + 活动消耗计算每日总消耗
- **个性化训练计划**：根据体重目标和当前运动水平自动生成
- **健康评分**：综合多项指标给出 0-100 分
- **报告导出**：生成可保存的分析报告

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/apple-health-analysis.git
cd apple-health-analysis

# 安装依赖（仅需 Python 标准库，无额外依赖）
# 如需导出报告，安装可选依赖：
pip install -r requirements.txt
```

### 使用

```bash
# 基础分析（终端输出）
python analyze.py /path/to/apple_health_export/

# 指定体重目标
python analyze.py /path/to/apple_health_export/ --target 72

# 生成完整报告文件
python analyze.py /path/to/apple_health_export/ --target 72 --output report.txt

# 只看最近 N 天的数据
python analyze.py /path/to/apple_health_export/ --days 30
```

### 如何导出 Apple Health 数据

1. 打开 iPhone 上的「健康」App
2. 点击右上角头像 → 「导出所有健康数据」
3. 等待导出完成，发送到电脑
4. 解压后得到 `apple_health_export` 文件夹

## 项目结构

```
apple-health-analysis/
├── analyze.py              # CLI 入口
├── lib/
│   ├── __init__.py
│   ├── parser.py           # Apple Health XML 流式解析
│   ├── metrics.py          # 健康指标计算与分析
│   ├── report.py           # 报告生成
│   └── training_plan.py    # 训练计划生成
├── configs/
│   ├── hermes/SKILL.md     # Hermes Agent 技能配置
│   ├── claude-code/        # Claude Code 技能配置
│   └── codex/AGENTS.md     # Codex 技能配置
├── requirements.txt
└── README.md
```

## AI Agent 集成

本工具支持三大 AI Agent 平台：

| 平台 | 配置文件 | 使用方式 |
|------|---------|---------|
| [Hermes Agent](https://hermes-agent.nousresearch.com) | `configs/hermes/SKILL.md` | 复制到 `~/.hermes/skills/` |
| [Claude Code](https://code.claude.com) | `configs/claude-code/apple-health.md` | 复制到 `.claude/skills/` |
| [Codex](https://github.com/openai/codex) | `configs/codex/AGENTS.md` | 复制到项目根目录 |

详见各配置文件内的说明。

## 隐私

- 所有分析在本地完成，数据不上传任何服务器
- Apple Health XML 文件不被修改或复制
- 报告文件仅保存在你指定的位置

## 数据说明

Apple Health 导出的 XML 文件通常很大（1-2GB），包含数百万条记录。本工具使用 `xml.etree.ElementTree.iterparse` 流式解析，内存占用低，解析速度快。

支持的指标：

| 指标 | Apple Health 类型 |
|------|------------------|
| 体重 | `HKQuantityTypeIdentifierBodyMass` |
| BMI | `HKQuantityTypeIdentifierBodyMassIndex` |
| 身高 | `HKQuantityTypeIdentifierHeight` |
| 步数 | `HKQuantityTypeIdentifierStepCount` |
| 活动能量 | `HKQuantityTypeIdentifierActiveEnergyBurned` |
| 运动时间 | `HKQuantityTypeIdentifierAppleExerciseTime` |
| 心率 | `HKQuantityTypeIdentifierHeartRate` |
| 静息心率 | `HKQuantityTypeIdentifierRestingHeartRate` |
| VO2Max | `HKQuantityTypeIdentifierVO2Max` |
| 飞行爬升 | `HKQuantityTypeIdentifierFlightsClimbed` |
| 步行距离 | `HKQuantityTypeIdentifierDistanceWalkingRunning` |
| 运动记录 | `Workout` |

## License

MIT
