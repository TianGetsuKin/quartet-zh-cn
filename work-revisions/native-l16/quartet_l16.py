#!/usr/bin/env python3
"""Install or restore the Quartet l16 native Linux patch using Python 3.8+."""

import argparse
import bz2
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent
BACKUP = ".quartet-l16-backup"
LOCK = ".quartet-l16-lock"
BLOCK = 1024 * 1024
MANIFEST = "manifest.json"
NEW_DLLS = {"Quartet.Chinese.dll", "Quartet.RecentItems.dll"}


def digest(path, algorithm):
    result = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(BLOCK), b""):
            result.update(data)
    return result.hexdigest()


def relative(path, first):
    item = PurePosixPath(path)
    if (item.is_absolute() or not item.parts or item.parts[0] != first
            or "\\" in path or ":" in path or ".." in item.parts or path != item.as_posix()):
        raise ValueError(f"无效路径 {path!r}")
    return item


def safe_path(root, name):
    path = root / name
    if path.resolve() != path:
        raise ValueError(f"拒绝经过符号链接或重定向的路径 {name}")
    return path


def read_manifest():
    raw = (HERE / MANIFEST).read_bytes()
    manifest = json.loads(raw)
    version = tuple(manifest.get(key) for key in ("game_version", "steam_build", "depot", "steam_manifest", "revision", "format"))
    if version != ("1.5.20261124", 26908524, 1307964, "2325920819324936782", "l16", "BSDIFF40"):
        raise ValueError("补丁清单版本不符")
    entries = manifest["files"]
    originals = [entry for entry in entries if entry["original_sha1"] is not None]
    additions = {PurePosixPath(entry["path"]).name for entry in entries if entry["original_sha1"] is None}
    filenames = {entry["path"].casefold() for entry in entries}
    payloads = {entry["payload"].casefold() for entry in entries}
    if len(entries) != 19 or len(originals) != 17 or additions != NEW_DLLS or len(filenames) != 19 or len(payloads) != 19:
        raise ValueError("补丁文件数量或成员不符")
    for entry in entries:
        relative(entry["path"], "QuartetLinux_Data")
        relative(entry["payload"], "payload")
        if entry["original_sha1"] is not None and not re.fullmatch(r"[a-f0-9]{40}", entry["original_sha1"]):
            raise ValueError("原件 SHA-1 无效")
        if not all(re.fullmatch(r"[a-f0-9]{64}", entry[key]) for key in ("result_sha256", "payload_sha256")):
            raise ValueError("载荷或目标 SHA-256 无效")
        if not isinstance(entry["result_bytes"], int) or entry["result_bytes"] <= 0:
            raise ValueError("目标文件大小无效")
    return entries, raw


def verify_install_inputs(root, entries):
    issues = []
    for entry in entries:
        path = safe_path(root, entry["path"])
        original = entry["original_sha1"]
        if original:
            if not path.is_file() or digest(path, "sha1") != original:
                issues.append(entry["path"])
        elif path.exists():
            issues.append(entry["path"] + "（新增文件应不存在）")
        payload = safe_path(HERE, entry["payload"])
        if not payload.is_file() or digest(payload, "sha256") != entry["payload_sha256"]:
            issues.append(entry["payload"] + "（补丁缺失或损坏）")
    if issues:
        raise ValueError("需要干净的原生 Linux 1.5.20261124 文件。校验失败：\n" + "\n".join(issues))


def verify_installed(root, entries):
    for entry in entries:
        path = safe_path(root, entry["path"])
        if not path.is_file() or path.stat().st_size != entry["result_bytes"] or digest(path, "sha256") != entry["result_sha256"]:
            raise ValueError(f"安装后校验失败 {entry['path']}")


@contextmanager
def lock_game(root):
    lock = safe_path(root, LOCK)
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError(f"安装目录已有事务锁 {lock}，请查看说明") from None
    try:
        yield
    finally:
        lock.rmdir()


def exact(stream, count):
    data = stream.read(count)
    if len(data) != count:
        raise ValueError("差分载荷提前结束")
    return data


def offset(data):
    position = int.from_bytes(data, "little", signed=False)
    return -(position & ((1 << 63) - 1)) if position >> 63 else position


def copy_exact(source, output, remaining):
    while remaining:
        count = min(remaining, BLOCK)
        output.write(exact(source, count))
        remaining -= count


def apply_bsdiff(original, delta, target, expected_size):
    """Decode signed-magnitude BSDIFF40 offsets and bzip2 streams with bounded reads."""
    patch = delta.read_bytes()
    if len(patch) < 32 or patch[:8] != b"BSDIFF40":
        raise ValueError("差分文件头无效")
    control_size, diff_size, output_size = (offset(patch[i:i+8]) for i in (8, 16, 24))
    end_control = 32 + control_size
    end_diff = end_control + diff_size
    if min(control_size, diff_size) < 0 or end_diff >= len(patch) or output_size != expected_size:
        raise ValueError("差分文件块长度无效")

    with bz2.BZ2File(io.BytesIO(patch[32:end_control])) as control, \
         bz2.BZ2File(io.BytesIO(patch[end_control:end_diff])) as diff, \
         bz2.BZ2File(io.BytesIO(patch[end_diff:])) as extra, \
         original.open("rb") as old, target.open("xb") as out:
        old_size = original.stat().st_size
        written = old_position = 0
        while written < output_size:
            length, extra_length, shift = (offset(exact(control, 8)) for _ in range(3))
            if min(length, extra_length) < 0 or written + length + extra_length > output_size:
                raise ValueError("差分控制块越界")
            remaining = length
            while remaining:
                count = min(remaining, BLOCK)
                change = exact(diff, count)
                lo = max(old_position, 0)
                hi = min(old_position + count, old_size)
                if lo < hi:
                    old.seek(lo)
                    existing = exact(old, hi - lo)
                    start = lo - old_position
                    delta_bytes = change[start:start + len(existing)]
                    if delta_bytes.count(0) == len(delta_bytes):
                        merging = existing
                    else:
                        merging = bytes((before + after) & 255 for before, after in zip(existing, delta_bytes))
                    change = change[:start] + merging + change[start + len(existing):]
                out.write(change)
                old_position += count
                remaining -= count
            copy_exact(extra, out, extra_length)
            old_position += shift
            written += length + extra_length
        if control.read(1) or diff.read(1) or extra.read(1):
            raise ValueError("差分载荷含多余数据")


def restore_locked(root, entries, raw):
    backup = safe_path(root, BACKUP)
    marker = safe_path(backup, MANIFEST)
    if not marker.is_file() or marker.read_bytes() != raw:
        raise ValueError("完整的 l16 备份标记缺失或不符")
    originals = backup / "original"
    to_restore = []
    to_remove = []
    for entry in entries:
        name = entry["path"]
        dest = safe_path(root, name)
        original = entry["original_sha1"]
        if original:
            saved = safe_path(originals, name)
            if not saved.is_file() or digest(saved, "sha1") != original:
                raise ValueError(f"备份校验失败 {name}")
            if dest.is_file() and digest(dest, "sha1") == original:
                continue
            if not dest.is_file() or digest(dest, "sha256") != entry["result_sha256"]:
                raise ValueError(f"游戏文件已被其他版本或补丁更改，暂停还原 {name}")
            to_restore.append((name, dest, saved))
        elif dest.exists():
            if not dest.is_file() or digest(dest, "sha256") != entry["result_sha256"]:
                raise ValueError(f"新增 DLL 已被更改，暂停还原 {name}")
            to_remove.append(dest)

    with tempfile.TemporaryDirectory(prefix="restore-", dir=backup) as temporary:
        for name, dest, saved in to_restore:
            staging = Path(temporary) / name
            staging.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, staging)
        for name, dest, _ in to_restore:
            os.replace(Path(temporary) / name, dest)
        for path in to_remove:
            path.unlink()

    for entry in entries:
        path = safe_path(root, entry["path"])
        original = entry["original_sha1"]
        if (original and digest(path, "sha1") != original) or (not original and path.exists()):
            raise ValueError(f"还原后校验失败 {entry['path']}")
    shutil.rmtree(backup)


def install_locked(root, entries, raw):
    backup = safe_path(root, BACKUP)
    if backup.exists():
        raise ValueError("已有 l16 备份，请先运行 restore")
    verify_install_inputs(root, entries)
    source_size = sum((root / entry["path"]).stat().st_size for entry in entries if entry["original_sha1"])
    needed = source_size + sum(entry["result_bytes"] for entry in entries)
    if shutil.disk_usage(root).free < needed + 16 * BLOCK:
        raise ValueError("游戏目录所在磁盘需要约 1.1 GB 可用空间制作新文件和备份")
    backup.mkdir()
    marker = backup / MANIFEST
    originals = backup / "original"
    try:
        with tempfile.TemporaryDirectory(prefix="install-", dir=backup) as temporary:
            for entry in entries:
                name = entry["path"]
                source = root / name
                result = Path(temporary) / name
                result.parent.mkdir(parents=True, exist_ok=True)
                payload = HERE / entry["payload"]
                original = entry["original_sha1"]
                if original:
                    saved = originals / name
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, saved)
                    if digest(saved, "sha1") != original:
                        raise ValueError(f"备份校验失败 {name}")
                    apply_bsdiff(saved, payload, result, entry["result_bytes"])
                    shutil.copystat(saved, result)
                else:
                    shutil.copyfile(payload, result)
                if result.stat().st_size != entry["result_bytes"] or digest(result, "sha256") != entry["result_sha256"]:
                    raise ValueError(f"准备好的文件校验失败 {name}")
            (backup / "manifest.tmp").write_bytes(raw)
            os.replace(backup / "manifest.tmp", marker)
            for entry in entries:
                os.replace(Path(temporary) / entry["path"], root / entry["path"])
            verify_installed(root, entries)
    except BaseException:
        if marker.is_file():
            try:
                restore_locked(root, entries, raw)
            except Exception as error:
                print(f"自动还原未完成，原件备份仍在 {backup}：{error}", file=sys.stderr)
        else:
            shutil.rmtree(backup)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "install", "restore"))
    parser.add_argument("game_dir", type=Path, help="包含 QuartetLinux_Data 的游戏目录")
    args = parser.parse_args()
    try:
        root = args.game_dir.expanduser().resolve(strict=True)
        if not (root / "QuartetLinux_Data").is_dir():
            raise ValueError("请选择含 QuartetLinux_Data 的原生 Linux 游戏目录")
        entries, raw = read_manifest()
        if args.action == "check":
            verify_install_inputs(root, entries)
            print("17 个游戏原件与 19 个差分或新增载荷校验通过。")
        else:
            with lock_game(root):
                if args.action == "install":
                    install_locked(root, entries, raw)
                    print("已安装 l16。19 个文件的 SHA-256 校验通过。")
                else:
                    restore_locked(root, entries, raw)
                    print("已还原 17 个官方原件。2 个汉化新增 DLL 已移除。")
    except KeyboardInterrupt:
        print("操作已中断。", file=sys.stderr)
        return 130
    except (OSError, ValueError, EOFError, KeyError, TypeError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
