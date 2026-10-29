# 用 REA 研究 Screen Studio 原生录制与导出

这是 Screen Studio **3.7.3-4540** 的逆向分析案例与只读工具集，面向研究
Electron 与 macOS 原生辅助程序的开发者和 Agent。仓库包含原创检查工具、
分级证据和复现方法；本地验证对象是原安装包的隔离副本，并非独立重写的软件。

[English README](README.md) · [证据与限制](docs/evidence.md)

## 已验证到哪里

- 隔离副本完成自身原生录制、生成项目、重启应用后打开、编辑和离线导出。
- 原生导出为 H.264、1104×720、60fps、3337 帧、55.616667 秒，完整解码通过。
- 后续真人操作记录到 938 个鼠标位置、15 次点击、10 次按键、1 段缩放；用户反馈功能正常。
- 联网授权验证失败。离线导出成功不能当作永久激活、服务端接受或联网稳定的证据。
- 只实测 Apple Silicon / macOS 26.5.2；未做整机冷启动，最终重签包也未重新走完整原生录制流程。

以上是 2026-10-29 的历史实验结论。为保护隐私，仓库只保留人工整理并去标识化的
[观测摘要](evidence/observations.json)，不发布原始视频、项目或机器日志，不能用本仓库独立重放历史实验。

## 本机检查

需要 Python 3.10+；仅使用标准库。视频核验另需 `ffprobe` 和 `ffmpeg`。

```bash
git clone https://github.com/Royo-Qiao/screenstudio-rea-research.git
cd screenstudio-rea-research
python3 scripts/inspect_app.py "/path/to/Screen Studio.app"
python3 scripts/project_stats.py "/path/to/Demo.screenstudio"
python3 scripts/verify_export.py "/path/to/export.mp4"
```

第一个命令读取版本、架构、系统声明、资源布局和哈希，不启动或修改目标应用。
第二个命令只输出鼠标、点击、按键和缩放统计，不输出按键内容、坐标或标题。
第三个命令要求文件非空、元数据有效、完整视频和音频解码无错误，并计算 SHA-256；
文件在核验期间变化会失败。所有命令输出 JSON，失败返回非零退出码。

检查视频有效性不等于证明它由 Screen Studio 自身录制，也不证明视觉效果一致。
请通过实际 UI 录制一次临时文件操作，保存原生项目，再进行编辑和导出。

## 复现与边界

按 [复现步骤](docs/reproduction.md) 使用自己的合法安装与授权，按需用
[REA](https://github.com/morluto/rea) 分析明确的本地目标。先确认版本和资源结构，
再把静态结论与运行时证据对应。完整项目只在本机保留。

仓库保留带真实 Evidence ID 的 REA
[Electron fuse](evidence/rea-fuses-summary.json) 与 [Mach-O](evidence/rea-macho-summary.json)
摘录；它们属于静态检查，不等于已完成原生函数反编译。

原应用声明最低 macOS 12.0；实验包内 Node 声明最低 13.5。二者都不能代替兼容性测试。
本项目不提供厂商应用、源码、授权响应或激活材料，不修改全局代理或系统安全设置。
原创工具与文档采用 MIT 许可，厂商产品权利归原权利人。
