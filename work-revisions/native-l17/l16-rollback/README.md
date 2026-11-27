# 还原已安装的《四重奏》原生 Linux l16

l16 可能在部分场景读取存档时崩溃。先退出游戏并还原 l16，然后安装同版本的 [l17 差分包](https://github.com/TianGetsuKin/quartet-zh-cn/releases/tag/1.5.20261124-zh-r30)。

游戏目录里有 `.quartet-l16-backup` 时，可使用原 l16 ZIP 解压后的脚本还原。原 ZIP 已删除的玩家，可将这一目录的 [quartet_l16.py](quartet_l16.py) 和 [manifest.json](manifest.json) 原样下载到同一个目录，然后在该处运行。

```sh
python3 ./quartet_l16.py restore "/游戏路径/Quartet"
```

清单须与备份中的版本逐字节匹配。使用 GitHub 文件页的 **Download raw file** 保存两份文件。此目录仅提供还原所需的脚本和校验清单。

如果备份缺失，先在 Steam「属性 → 已安装文件」验证游戏文件完整性。再核对 `QuartetLinux_Data/Managed` 中的两个 l16 新增 DLL，只把 SHA-256 匹配的残留文件移出游戏目录。 [文件名及指纹](../README.txt)

还原官方文件后，按 l17 包内说明先运行 `check`，通过后再运行 `install`。
