# 《四重奏》1.5.20261124 Windows 汉化更新（r30）

对应 Windows Steam build 26908524，内容清单 8712119740688563894（depot 1307962）。上一版 r29 / l15 对应游戏 1.5.20260912，Windows build 25279268。原生 Linux 尚未适配这次游戏更新。

## 修改与证据

- 以两份 Windows Steam 清单核对原始输入。旧补丁覆盖的 16 个官方文件中 12 个已更新，另有 2 个补丁 DLL。新清单和两个资源包的新文件名见 windows-depot-diff.json。
- 官方只更改了一个有名的 Yarn 程序节点 battle_liganti1。新版官方放宽了原先精确相等的判断。r30 的场景包和全局资源都采用新版完整编译剧情，两份程序的 SHA-256 和新版原文件相同。保留中文文本，停用旧版为戈登行动加的兜底分支。
- 在新版 Unity 资源上合并中文改动，保留序章首领各难度的新版数据。resources.assets 和共享场景的对象重新匹配。保留官方 IL2CPP 元数据和可执行文件，再迁移汉化用字符串、原生调用和辅助 DLL。
- Windows 语言运行库 22 项测试、最近获得装备的原生逻辑夹具、Windows 加载三份补丁 DLL、Unity 容器回读、ZIP 逐文件解压与隔离覆盖还原均已检查。未运行游戏内视觉或剧情全流程。玩家机器未安装本次候选。
- 版本、载荷及 SHA-256、归档指纹见 release-r30.json。维护目录只存本次增量和核验记录，玩家包单独提供。沿用此前的权威译稿。

## 在原工程重建

使用 Windows x64、Python 3.11 或更新、UnityPy 1.25.3、capstone 5.0.6、numpy 1.26.4，以及项目原有 GCC、rustc。脚本使用当前文件位置和相邻历史工程定位既有输入。在其他电脑需还原目录结构或适配 compare_depots.py 中的路径。当前只在原维护机运行过。

1. 将本目录放到 Quartet-zh-pending/rebased-26908524。相邻目录应有 rebased-25279268（原权威译稿、备份和各修订维护源码）及 build-25279268-snapshot/GameAssembly.dll。游戏原版新文件在 Quartet-zh-pending 的同级 Quartet 文件夹。两份 depot 清单取自 Steam 的 depotcache。r29.json 对应的旧 ZIP 需可读，并保留 r23/r26/r27 的历史构建依赖。
2. 在此目录用上述 Python 环境依次运行 compare_depots.py、compare_yarn.py、migrate_assets.py、migrate_metadata.py。
3. 依次运行 native_images.py、native_map.py、rebase_native.py、build_helpers.py。核对 native-address-audit.json 无空地址，asset-audit.json 各项已回读或源文件相同。重新构建辅助 DLL 的工具链时间戳可能影响成品散列。
4. 运行 verify_update.py，然后运行 package_windows.py。后者写入 r29 ZIP 所在的交付文件夹，从实际 ZIP 解压全部载荷、还原 Steam 原版并核对。正式游戏目录只用于读取。
5. 以 release-r30.json 核对成品；玩家使用 ZIP 内的使用说明。实机优先回归从正常入口启动、中英文、二周目科黛莉娅速度 10/11 的教学战、序章首领虚弱姿态，以及最近获得的换装焦点。Steam Deck 需等待对应原生新版输入，分别迁移与验证。

此目录不含 Steam 原游戏、玩家存档或账号数据。公开仓库沿用既有发布形式及素材分发范围。

公开 Release 重新打包时更新了版本兼容提示与公告链接，中文载荷与已验证的 r30 构建完全一致。使用 Release ZIP 覆盖 16 个新版原文件并回读 18 个载荷，随后还原原文件通过。完整归档信息见 release-r30.json。
