# 《四重奏》1.5.20261124 原生 Linux / Steam Deck 汉化补丁 l16

**l16 已由 l17 取代。** l16 可能在部分场景读档时崩溃。已安装的玩家请参考 [l16 升级与还原说明](../native-l17/l16-rollback/)。以下为 l16 的历史构建记录。

对应 Steam Build 26908524，Linux depot 1307964，清单 2325920819324936782。l15 仅适用于游戏 1.5.20260912（清单 2670900619531972171）。Windows 同版本使用 r30。

## 构建与核验

本目录位于 windows r30 维护目录 rebased-26908524 下，与 rebased-25279268 中既有 Linux 源码和翻译共同构建。使用 Python 3.11+、UnityPy 1.25.3、原项目锁定的 Mono.Cecil 0.11.6、Windows Framework64 csc 和 PowerShell。仅在原维护机完成构建。公共源码不含 Steam 原文件、个人档案和设备凭据。

1. 在本目录准备上述两份官方 Linux depot 清单，以及 input/ 中本次改变的 12 个原版文件。保留旧工程 linux-native/input/build25279268、历史 l10 和 l15 包、native-l11 及后续修订的源码和构建输入。旧 SHA 与新 SHA 分别取自对应的完整 Steam 清单。pack_l16.clean() 给出当前平台 17 个干净原文件的逐项位置。
2. 运行 assets_l16.py，将 Linux l15 中文资源合入新版原生资源。既有翻译对象与新版按内容、类型、脚本、名称或场景层级匹配。sharedassets4 中还有没有场景实体的 ScriptableObject，以其名称与脚本匹配。保留两份完整的新版编译剧情，其他译文从上版沿用。
3. 运行 build_managed.py，在新旧干净的 Assembly-CSharp.dll 上分别按原顺序重放语言、最近获得、装备及商店补丁。将原维护目录的 Mono.Cecil.dll 放入本目录，以 csc /target:library /reference:Mono.Cecil.dll /out:CompareIL.dll CompareIL.cs 编译语义比对工具，随后运行 check-managed.ps1。
4. 同一流水线在旧版重建的游戏程序集与 l15 的类、字段、属性、方法指令及异常处理比较无差异。新版官方变更的 12 个声明或方法与汉化改动零重叠，其中包括 BattleActorManager.Start 和 BattleTime.Tick。既有实际托管逻辑测试覆盖调用、跳转、历史记录、库存和标签。
5. 在原维护树运行 pack_l16.py，核对 19 个载荷、中文资源回读、两份 Yarn 程序的 SHA-256 以及本地覆盖还原。此目录的 release-l16.json 保留原件和输出指纹。Deck 的游戏画面与利甘蒂实战交玩家继续验证。

玩家使用同版本 [GitHub Release](https://github.com/TianGetsuKin/quartet-zh-cn/releases/tag/1.5.20261124-zh-r30) 内的 l17 原生 Linux 差分包。l16 发布包原先用 17 个原版文件生成差分，另含 2 个本项目的新增托管 DLL。


仓库展示的是原维护树中的脚本和核验记录。按原结构将本目录放在 rebased-26908524 下，compare_depots.py 随 [Windows r30 维护记录](../windows-r30/) 保存。输入需由有权访问游戏的维护者准备。公开快照可用于核对和接手，完整重建目前只在原维护树验证。

差分包构建器为 prepare_delta.py，需 Python 3.11 及 bsdiff4，并以准备完成的原维护树为输入。根目录中的 delta-manifest.json 是构建记录。玩家还原时使用从公开包原样提取的清单与脚本。 [l16 还原工具](../native-l17/l16-rollback/)
