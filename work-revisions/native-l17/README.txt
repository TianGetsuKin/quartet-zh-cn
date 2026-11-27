《四重奏》简体中文补丁 l17
Steam Deck／原生 Linux，游戏 1.5.20261124

适配 Steam Build 26908524、Linux depot 1307964、清单 2325920819324936782。
l17 修复 l16 在部分场景读取存档时可能崩溃的问题。已经使用 l16 的玩家请升级。
Steam Deck 使用原生 Linux 版时安装 l17。Windows 或强制使用 Proton 时，使用 Windows r30。
游戏旧版 1.5.20260912 对应 l15。

从 l16 升级

先退出游戏。保留游戏目录中的 .quartet-l16-backup，如果仍在，在解压后的 l16 补丁目录运行原安装脚本还原：

   python3 ./quartet_l16.py restore "/游戏路径/Quartet"

如果 l16 备份缺失，先通过 Steam「属性 → 已安装文件 → 验证游戏文件的完整性」恢复官方文件。
然后查看游戏目录下 QuartetLinux_Data/Managed 中是否还有下列两个 l16 新增 DLL。
用 sha256sum 核对，逐个只将与下列指纹完全相符的残留文件移出游戏目录。遇到指纹不同的文件先保留。

   Quartet.Chinese.dll      54d7767cde62095f4ce3262bf493d9be5fceef57b802510bff1bf1c2948944a8
   Quartet.RecentItems.dll  e1f1bbc83e08c259788bcd9587c8fff229dfc5a9ab9bcec146c02c60acd0ee1a

完成上述任一恢复方式后，按下文先运行 l17 的 check。检查通过后再安装。

安装

1. 退出游戏，在 Steam 游戏属性的「已安装文件」打开游戏文件夹，确认内含 QuartetLinux_Data。
2. 完整解压 ZIP，在解压目录打开终端。需要 Python 3.8 或更新版本，可用 python3 --version 检查。
3. 游戏所在磁盘建议预留约 1.1 GB 给原件备份和临时数据。将下方引号内替换为实际游戏路径，逐条运行。

   python3 ./quartet_l17.py check "/游戏路径/Quartet"
   python3 ./quartet_l17.py install "/游戏路径/Quartet"

安装器校验 17 个原版文件的指纹及 19 个载荷。准备并校验所有结果后才逐个换入。

还原

保留此解压目录和游戏目录下的 .quartet-l17-backup。退出游戏后运行：

   python3 ./quartet_l17.py restore "/游戏路径/Quartet"

还原会校验备份并恢复 17 个原件，移除 2 个由本补丁新增且指纹匹配的 DLL。
如果文件已被游戏更新或其他补丁改动，请保留备份并按当前游戏版本核对。

安装中断

安装器若提示自动还原未完成，请保留备份并重试 restore。若终端被强制关闭，确认安装器和游戏均已退出后，可只移除游戏目录内的空目录 .quartet-l17-lock，再运行 restore。
如果缺少完整的备份标记，先运行 check 核实原版文件。确认文件为干净原版后，可将残留的 .quartet-l17-backup 移出游戏目录，再重新安装。

验证

发行包在隔离的原版文件副本上验证了 l16 安装、还原后换装 l17、l17 安装和还原，19 个补丁文件的 SHA-256 和 17 个还原文件的 Steam SHA-1 均匹配。
维护者在 Steam Deck 用同一份存档副本复现 l16 读档崩溃，并确认 l17 能进入原场景继续运行。
新版游戏内的画面和利甘蒂实战仍待玩家验证。字体授权见 OFL.txt。
