# 《四重奏》原生 Linux l17

适用游戏 1.5.20261124，Steam Build 26908524，Linux depot 1307964，清单 2325920819324936782。玩家从 GitHub Release 下载补丁。 [下载页](https://github.com/TianGetsuKin/quartet-zh-cn/releases/tag/1.5.20261124-zh-r30) · [安装说明](README.txt)

已安装 l16 的玩家可先还原旧版，再安装 l17。 [l16 还原说明](l16-rollback/)

l16 为让换装辅助程序集访问 `FieldMenuEquipController.selectedSlot`，将该字段改为 public。Unity 随之将该字段纳入序列化，而官方场景的数据仍采用原布局。l17 保留所需的访问级别，并显式排除该字段和两个运行时对话引用的序列化。

## 构建

1. 按 [l16 构建记录](../native-l16/) 准备官方原件与已构建的 l16 工作树。保持工作目录结构，让 l16 目录名为 `linux-l16`，并将 `fix.ps1` 放入同级的 `linux-l17`。
2. 使用 l16 工作树的 Mono.Cecil 0.11.6 和 CompareIL，并运行 `fix.ps1`。脚本将修正结果写入 `stage/QuartetLinux_Data/Managed/Assembly-CSharp.dll`，并验证改动限制在指定的三个字段。
3. 以对应 Steam 原版 Assembly-CSharp.dll 为输入，以修正后的程序集为目标生成 BSDIFF40 差分。其余 18 个载荷沿用 l16。按 [manifest.json](manifest.json) 的路径收录载荷和对应安装器，核对原件、载荷和输出散列。

此目录随版本保留玩家侧的差分安装和还原源码，以及构建与核验所需的清单。原件由维护者从其 Steam 安装准备。

## 核验

Steam Deck 使用同一份存档副本核对转场，l16 在读档时崩溃，l17 成功进入场景并继续运行。隔离安装验证覆盖了 l16 还原、l17 安装及回滚，19 个补丁文件和 17 个还原原件的散列均匹配。新版画面及利甘蒂实战仍待玩家验证。 [文件核验记录](verification.json)
