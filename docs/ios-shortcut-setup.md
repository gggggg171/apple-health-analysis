# iOS 快捷指令配置指南

通过 iPhone 快捷指令自动导出 Apple Health 数据到 iCloud Drive，
配合 Mac 端的 `--watch` 模式实现每日自动分析。

## 第一步：创建 iCloud 同步文件夹

在 Mac 上创建监控目录：

```bash
mkdir -p ~/Library/Mobile\ Documents/com~apple~CloudDocs/HealthExport
```

这个目录会通过 iCloud Drive 自动在 iPhone 和 Mac 之间同步。

## 第二步：在 iPhone 上创建快捷指令

### 2.1 打开快捷指令 App

iPhone 上打开「快捷指令」（Shortcuts）App，点击右上角 `+` 新建。

### 2.2 添加操作

按顺序添加以下操作（在搜索框中搜索操作名称）：

#### 操作 1：获取健康样本
1. 搜索「健康」→ 选择「获取健康样本的类型」
2. 样本类型选择「步骤」
3. 日期范围：选择「过去 7 天」（或你想要的范围）

> **注意**：iOS 快捷指令对健康数据的直接导出支持有限。
> 更完整的方案见下方「推荐替代方案」。

### 推荐替代方案：使用 Health Auto Export

由于 iOS 快捷指令对健康数据导出的支持比较有限，推荐使用免费 App：

#### 方案 A：Health Auto Export（推荐）

1. 在 App Store 搜索并安装 **Health Auto Export**（免费版即可）
2. 打开 App → 允许访问健康数据
3. 设置：
   - 导出格式：**JSON**
   - 保存位置：**iCloud Drive**
   - 文件夹：**HealthExport**（即上面创建的目录）
   - 自动导出：**开启**
   - 频率：**每天**

#### 方案 B：快捷指令 + 手动触发

如果不想装第三方 App，可以创建一个手动触发的快捷指令：

1. 打开「快捷指令」→ 新建
2. 搜索添加以下操作：
   - 「健康」→「获取健康样本的类型」（每种类型各加一个）
   - 「文件」→「保存文件」→ 选择 iCloud Drive/HealthExport

3. 命名为「导出健康数据」
4. 每天手动运行一次，或设置自动化定时提醒

## 第三步：Mac 端启动监控

在 Mac 终端中运行：

```bash
cd /path/to/apple-health-analysis

# 启动监控（每 60 秒检查一次，目标体重 72kg）
python analyze.py ~/Library/Mobile\ Documents/com~apple~CloudDocs/HealthExport/ \
    --watch --target 72 --html --interval 60
```

### 后台运行

```bash
# 使用 nohup 后台运行
nohup python analyze.py ~/Library/Mobile\ Documents/com~apple~CloudDocs/HealthExport/ \
    --watch --target 72 --html --interval 300 > ~/health_watch.log 2>&1 &

# 查看日志
tail -f ~/health_watch.log

# 停止后台进程
pkill -f "analyze.py.*--watch"
```

### 开机自启（可选）

创建 LaunchAgent 实现开机自动启动监控：

```bash
cat > ~/Library/LaunchAgents/com.apple-health-watch.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple-health-watch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/USERNAME/apple-health-analysis/analyze.py</string>
        <string>/Users/USERNAME/Library/Mobile Documents/com~apple~CloudDocs/HealthExport</string>
        <string>--watch</string>
        <string>--target</string>
        <string>72</string>
        <string>--html</string>
        <string>--interval</string>
        <string>300</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/USERNAME/health_watch.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/USERNAME/health_watch.log</string>
</dict>
</plist>
EOF

# 替换 USERNAME 为你的用户名
sed -i '' "s/USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.apple-health-watch.plist

# 加载
launchctl load ~/Library/LaunchAgents/com.apple-health-watch.plist

# 卸载
# launchctl unload ~/Library/LaunchAgents/com.apple-health-watch.plist
```

## 完整工作流

```
iPhone                          iCloud Drive                    Mac
┌──────────────┐               ┌──────────────┐           ┌──────────────┐
│  Apple Health │               │              │           │              │
│     数据      │──自动导出──→  │ HealthExport │──同步──→  │ --watch 模式 │
│              │  (每天定时)    │   /data.zip  │           │  自动检测分析 │
└──────────────┘               └──────────────┘           └──────┬───────┘
                                                                 │
                                                    ┌────────────▼───────────┐
                                                    │   reports/             │
                                                    │   ├── latest.html      │
                                                    │   └── health_*.html    │
                                                    └────────────────────────┘
```

## 常见问题

**Q: iCloud 同步延迟怎么办？**
A: 设置 `--interval 300`（5分钟检查一次），给同步留足时间。

**Q: 导出文件很大怎么办？**
A: Apple Health 导出通常是 zip 格式，工具会自动解压分析后清理临时文件。

**Q: 如何查看报告？**
A: 报告保存在 `HealthExport/reports/` 目录下，`latest.html` 始终指向最新报告。
   双击即可在浏览器中打开。

**Q: 多天的数据会冲突吗？**
A: 不会。工具通过文件名和修改时间判断是否已处理，每个导出文件独立分析。
