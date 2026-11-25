# 《四重奏》（Quartet）简体汉化维护

游戏 AppID 为 `1307960`，Steam Build `25279268`。对应 [官方游戏更新 1.5.20260912](https://store.steampowered.com/news/app/1307960/view/1843481262700116)。Windows 使用 **r29**，原生 Linux 和原生 Steam Deck 使用 **l15**。

这一轮让「最近获得」进入装备比较时直接定位选中的装备，同时保留游戏的原始列表顺序。两个 ZIP 都完成回读。Windows 菜单离线回归通过。Linux 已核对调用点，完整菜单夹具与两端最新版本的实机显示仍待验证。

## 接手

- `translations/` 保留现行原生译稿。对白按稳定行标识处理，校对时保持角色前缀、控制标记、换行、变量和事件顺序。资源显示、运行时文字和字体在各自构建入口验证。
- `tools/` 保留对白、资源、界面构建入口及原工程的差分工具源码。上游原始 Unity 文件待用所购游戏固定到相同 Build，各平台的输入不能混用。
- [r29 / l15 构建记录](work-revisions/equip-focus-r29-l15/) 包含最近获得改动、源代码和回读结果。增量构建需要对应 r28、l14 基线与原工程的编译依赖，涉及 Python、GCC、C# 编译器和对应的 Unity 托管库。此快照未验证在另一台机器从净输入一键重建。
- [四界图志](atlas/index.html) 可离线打开。地点与点位修改 `atlas/data/points.js`，瓦片编码在 `atlas/data/tiles.js`，素材在 `atlas/assets/`。原打包与取数方法见 `atlas/generator/`，涉及 Pillow 和 UnityPy，重抽游戏图需要对应正版资源和原项目数据。日常改地点、图层与提示时可直接编辑拆分文件。
