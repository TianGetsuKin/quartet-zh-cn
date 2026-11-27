"""Build the l16 BSDIFF40 payload from fingerprinted maintenance inputs."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
from zipfile import ZIP_DEFLATED, ZipFile


HERE = Path(__file__).resolve().parent
PACKAGE = "quartet-zh-cn-linux-l16-delta.zip"


def digest(path, algorithm):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, algorithm).hexdigest()


def build_payload(source):
    sys.path[:0] = [str(HERE / ".build-deps"), str(source)]
    import bsdiff4
    from base import PREV, PRISTINE

    def clean(name):
        candidates = [source / "input" / name, PRISTINE / name]
        if name.endswith("/sharedassets7.assets.resS"):
            candidates.append(PREV / "work-revisions/native-l11/stage/sharedassets7.assets.resS")
        return next(path for path in candidates if path.is_file())

    release = json.loads((source / "release-l16.json").read_bytes())
    assert (release["game_version"], release["steam_build"], release["depot"], release["revision"]) == (
        "1.5.20261124", 26908524, 1307964, "l16"
    )
    assert len(release["steam_sha1"]) == 17 and len(release["files"]) == 19
    for name, expected in release["steam_sha1"].items():
        assert digest(clean(name), "sha1") == expected, name
    for name, expected in release["files"].items():
        assert digest(source / "stage" / name, "sha256") == expected, name

    work = HERE / ".payload-work"
    work.mkdir(exist_ok=True)
    entries = []
    for index, (name, expected) in enumerate(release["files"].items(), 1):
        original_sha = release["steam_sha1"].get(name)
        filename = f"{index:02d}." + ("bsdiff" if original_sha else "dll")
        dest = work / filename
        result = source / "stage" / name
        print(f"[{index}/19] {PurePosixPath(name).name}", flush=True)
        if original_sha:
            bsdiff4.file_diff(str(clean(name)), str(result), str(dest))
        else:
            assert PurePosixPath(name).name in {"Quartet.Chinese.dll", "Quartet.RecentItems.dll"}
            shutil.copyfile(result, dest)
        entries.append({
            "path": name,
            "payload": f"payload/{filename}",
            "payload_sha256": digest(dest, "sha256"),
            "original_sha1": original_sha,
            "result_sha256": expected,
            "result_bytes": result.stat().st_size,
        })
        print(f"  {dest.stat().st_size:,} bytes", flush=True)
    receipt = {
        "game_version": release["game_version"],
        "steam_build": release["steam_build"],
        "depot": release["depot"],
        "steam_manifest": "2325920819324936782",
        "revision": release["revision"],
        "format": "BSDIFF40",
        "files": entries,
    }
    (HERE / "manifest.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    original_archive = Path(release["archive"])
    assert digest(original_archive, "sha256") == release["archive_sha256"]
    with ZipFile(original_archive) as zip_file:
        (HERE / "OFL.txt").write_bytes(zip_file.read("OFL.txt"))


def assemble():
    entries = json.loads((HERE / "manifest.json").read_bytes())["files"]
    temporary = HERE / (PACKAGE + ".tmp")
    with ZipFile(temporary, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for name in ("README.txt", "OFL.txt", "manifest.json", "quartet_l16.py"):
            archive.write(HERE / name, name)
        for file in entries:
            src = HERE / ".payload-work" / PurePosixPath(file["payload"]).name
            assert digest(src, "sha256") == file["payload_sha256"]
            archive.write(src, file["payload"])
    with ZipFile(temporary) as archive:
        assert len(archive.namelist()) == 23 and archive.testzip() is None
    result = HERE / PACKAGE
    temporary.replace(result)
    print(f"{result.name} {result.stat().st_size} {digest(result, 'sha256')}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--assemble", action="store_true")
    args = parser.parse_args()
    if args.source is None and not args.assemble:
        parser.error("specify --source and/or --assemble")
    if args.source is not None:
        build_payload(args.source.resolve(strict=True))
    if args.assemble:
        assemble()


if __name__ == "__main__":
    main()
