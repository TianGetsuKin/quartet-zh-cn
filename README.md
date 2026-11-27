# 《四重奏》（Quartet）简体汉化维护

游戏 Steam AppID 为 `1307960`。按平台和游戏版本下载对应补丁。

| 平台 | 游戏版本 | 汉化版本与下载 |
| --- | --- | --- |
| Windows x64 | [1.5.20261124](https://store.steampowered.com/news/app/1307960/view/1850460852983911) · Steam Build `26908524` | [r30 完整覆盖包](https://github.com/TianGetsuKin/quartet-zh-cn/releases/tag/1.5.20261124-zh-r30) |
| 原生 Linux／Steam Deck | 1.5.20261124 · Steam Build `26908524` | [l16 差分包](https://github.com/TianGetsuKin/quartet-zh-cn/releases/tag/1.5.20261124-zh-r30) |
| 原生 Linux／Steam Deck | 1.5.20260912 | [l15 旧版完整覆盖包](https://github.com/TianGetsuKin/quartet-zh-cn/releases/tag/1.5.20260912-zh-r29-l15) |

Windows r30 保留新版利甘蒂战斗剧情和序章首领虚弱姿态，并沿用中文与「最近获得」装备比较定位。已核对新版剧情字节码、Unity 资源、三份 Windows DLL 加载、22 项语言运行库测试及装备菜单离线逻辑。公开 ZIP 在隔离目录对 16 个干净原版文件完成覆盖、18 个补丁载荷 SHA-256 回读与还原。新版游戏内战斗和画面尚待实机核验，Windows r30 尚未在 Deck／Proton 上验证。

原生 Linux l16 从 17 个干净的原版文件打差分，安装后核对 19 个文件。隔离安装与回滚均通过，Deck 上的 l16 文件也已回读核对。新版的画面和利甘蒂实战待玩家验证。l15 仅适用于旧版。Steam Deck 使用 Proton 时适用 Windows 包。

## 接手

- [原生 Linux l16 维护记录](work-revisions/native-l16/) 保留原件与载荷指纹、托管代码及资源核验，以及差分构建、安装和回滚源码。
- [Windows r30 构建记录](work-revisions/windows-r30/) 包含新版的原版指纹、资源与剧情比对、原生定位、辅助 DLL 源码和离线验证结果。权威译稿沿用仓库现有版本。重建仍依赖相邻历史工程和对应的正版 Steam 文件，已在原维护机验证。
- `translations/` 保留现行原生译稿。对白按稳定行标识处理，校对时保持角色前缀、控制标记、换行、变量和事件顺序。资源显示、运行时文字和字体在各自构建入口验证。
- `tools/` 保留对白、资源、界面构建入口及原工程的差分工具源码。上游原始 Unity 文件待用所购游戏固定到相同 Build，各平台的输入不能混用。
- [r29 / l15 构建记录](work-revisions/equip-focus-r29-l15/) 包含最近获得改动、源代码和回读结果。增量构建需要对应 r28、l14 基线与原工程的编译依赖，涉及 Python、GCC、C# 编译器和对应的 Unity 托管库。此快照未验证在另一台机器从净输入一键重建。
- [四界图志](atlas/index.html) 可离线打开。地点与点位修改 `atlas/data/points.js`，瓦片编码在 `atlas/data/tiles.js`，素材在 `atlas/assets/`。原打包与取数方法见 `atlas/generator/`，涉及 Pillow 和 UnityPy，重抽游戏图需要对应正版资源和原项目数据。日常改地点、图层与提示时可直接编辑拆分文件。
