# iOS 快捷指令配置指南

通过 iPhone 快捷指令实现两种数据同步方式：

- **方式 A**：快捷指令每日自动查询关键数据 → JSON → iCloud → Mac 自动分析
- **方式 B**：手动导出完整数据 → zip → iCloud → Mac 自动分析

---

## 方式 A：快捷指令每日自动查询（全自动）

### 第一步：在 Mac 上创建同步文件夹

```bash
mkdir -p ~/Library/Mobile\ Documents/com~apple~CloudDocs/HealthExport/daily
```

### 第二步：在 iPhone 上创建快捷指令

打开「快捷指令」App → 点击右上角 `+` → 按以下步骤添加操作：

#### 操作 1：获取当前日期
1. 搜索「日期」→ 添加「当前日期」
2. 搜索「格式化日期」→ 添加，格式选「自定义」
3. 格式字符串输入：`yyyy-MM-dd`
4. 连接到「当前日期」

#### 操作 2：查询步数
1. 搜索「健康」→ 添加「查找健康样本」
2. 类型选「步数」
3. 添加过滤条件：「开始日期」→「是」→「今天」
4. 添加「统计」操作 → 选「求和」→ 连接到健康样本结果

#### 操作 3：查询体重
1. 搜索「健康」→ 添加「查找健康样本」
2. 类型选「体重」
3. 添加过滤条件：「开始日期」→「是」→「今天」
4. 排序：「开始日期」→ 降序
5. 限制：1 条

#### 操作 4：查询静息心率
1. 搜索「健康」→ 添加「查找健康样本」
2. 类型选「静息心率」
3. 添加过滤条件：「开始日期」→「是」→「今天」
4. 排序：「开始日期」→ 降序
5. 限制：1 条

#### 操作 5：查询活动能量
1. 搜索「健康」→ 添加「查找健康样本」
2. 类型选「活动能量」
3. 添加过滤条件：「开始日期」→「是」→「今天」
4. 添加「统计」操作 → 选「求和」

#### 操作 6：查询运动时间
1. 搜索「健康」→ 添加「查找健康样本」
2. 类型选「Apple 运动时间」
3. 添加过滤条件：「开始日期」→「是」→「今天」
4. 添加「统计」操作 → 选「求和」

#### 操作 7：查询锻炼记录
1. 搜索「健康」→ 添加「查找锻炼」
2. 添加过滤条件：「开始日期」→「是」→「今天」

#### 操作 8：构建 JSON 并保存
1. 搜索「文本」→ 添加「文本」操作
2. 输入以下模板（用变量替换占位符）：

```json
{
  "export_date": "格式化日期结果",
  "days": [
    {
      "date": "格式化日期结果",
      "steps": 步数求和结果,
      "weight_kg": 体重值,
      "resting_heart_rate": 静息心率值,
      "active_energy_kcal": 活动能量求和结果,
      "exercise_minutes": 运动时间求和结果,
      "workouts": [
        {
          "type": "锻炼类型",
          "duration_min": 锻炼时长,
          "kcal": 锻炼卡路里
        }
      ]
    }
  ]
}
```

3. 搜索「文件」→ 添加「保存文件」
4. 位置选：`iCloud Drive/HealthExport/daily/`
5. 文件名输入：`health_格式化日期结果.json`
6. 关闭「询问存储位置」

#### 操作 9：运行脚本（可选，需要 Mac 在线）
1. 搜索「SSH」→ 添加「通过 SSH 运行脚本」
2. 主机：你的 Mac IP 地址
3. 用户：你的 Mac 用户名
4. 输入：
```bash
cd ~/Desktop/Hermes文件/apple-health-analysis && python analyze.py ~/Library/Mobile\ Documents/com~apple~CloudDocs/HealthExport/daily/ --html
```

### 第三步：设置自动化运行

1. 打开「快捷指令」App → 底部「自动化」标签
2. 点击 `+` → 「创建个人自动化」
3. 选「特定时间」→ 设置每天（如 22:00）
4. 选择刚才创建的快捷指令
5. 关闭「运行前询问」

### 第四步：Mac 端启动监控

```bash
cd ~/Desktop/Hermes文件/apple-health-analysis

# 监控 daily 目录中的 JSON 文件
python analyze.py ~/Library/Mobile\ Documents/com~apple~CloudDocs/HealthExport/daily/ \
    --watch --target 72 --html --interval 300
```

---

## 方式 B：手动导出完整数据（每周一次）

### 第一步：在 iPhone 上导出

1. 打开「健康」App
2. 点击右上角头像
3. 点击「导出所有健康数据」
4. 选择「存储到"文件"」
5. 选择 `iCloud Drive/HealthExport/` 文件夹
6. 点击「存储」

### 第二步：Mac 端自动处理

同上，`--watch` 模式会自动检测新的 zip 文件并分析。

---

## 完整工作流

```
方式 A（每日自动）:
iPhone 快捷指令 → 查询数据 → 保存 JSON → iCloud 同步 → Mac --watch → HTML 报告

方式 B（每周手动）:
iPhone 健康 App → 导出 zip → iCloud 同步 → Mac --watch → 完整 HTML 报告
```

## 注意事项

1. **快捷指令查询的数据不如 XML 导出完整**——缺少 VO2Max、飞行爬升等字段
2. **JSON 格式每天一个文件**，工具会自动合并分析
3. **iCloud 同步可能有延迟**，设置 `--interval 300`（5分钟）给同步留时间
4. **首次运行需要授权**——快捷指令会请求健康数据访问权限
5. **方式 A 和 B 可以同时使用**——JSON 做日常监控，zip 做完整分析
