#!/usr/bin/env python3
"""Read bundle declarations and Mach-O load commands without launching the app."""
import argparse
import hashlib
import json
import platform
import plistlib
import shutil
import struct
import subprocess
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def version_string(value):
    return f"{value >> 16}.{(value >> 8) & 255}.{value & 255}"


def macho_slices(path):
    """Parse bounded thin/fat headers; declarations are not compatibility tests."""
    size = path.stat().st_size
    with path.open("rb") as source:
        def read_at(offset, length):
            if offset < 0 or length < 0 or offset + length > size:
                raise ValueError("Truncated Mach-O file")
            source.seek(offset)
            data = source.read(length)
            if len(data) != length:
                raise ValueError("Truncated Mach-O file")
            return data

        magic = read_at(0, 4)
        fat = {b"\xca\xfe\xba\xbe": (">", False), b"\xbe\xba\xfe\xca": ("<", False),
               b"\xca\xfe\xba\xbf": (">", True), b"\xbf\xba\xfe\xca": ("<", True)}
        if magic in fat:
            endian, wide = fat[magic]
            count = struct.unpack(endian + "I", read_at(4, 4))[0]
            if count > 64:
                raise ValueError("Unreasonable Mach-O slice count")
            offsets = []
            for index in range(count):
                row = read_at(8 + index * (32 if wide else 20), 32 if wide else 20)
                if wide:
                    _, _, offset, length, _, _ = struct.unpack(endian + "IIQQII", row)
                else:
                    _, _, offset, length, _ = struct.unpack(endian + "IIIII", row)
                if offset + length > size or length < 28:
                    raise ValueError("Invalid Mach-O slice range")
                offsets.append((offset, length))
        else:
            offsets = [(0, size)]
        result = []
        for start, length in offsets:
            magic = read_at(start, 4)
            thin = {b"\xcf\xfa\xed\xfe": ("<", 32), b"\xfe\xed\xfa\xcf": (">", 32),
                    b"\xce\xfa\xed\xfe": ("<", 28), b"\xfe\xed\xfa\xce": (">", 28)}
            if magic not in thin:
                raise ValueError("Not a supported Mach-O executable")
            endian, header_size = thin[magic]
            header = struct.unpack(endian + "6I", read_at(start + 4, 24))
            cpu, subtype, _, ncmds, command_bytes, _ = header
            if ncmds > 65536 or command_bytes > 16 * 1024 * 1024:
                raise ValueError("Unreasonable Mach-O load-command table")
            end = start + header_size + command_bytes
            if header_size + command_bytes > length:
                raise ValueError("Mach-O commands exceed slice")
            cursor = start + header_size
            minimum = None
            sdk = None
            for _ in range(ncmds):
                if cursor + 8 > end:
                    raise ValueError("Truncated Mach-O load command")
                command, command_size = struct.unpack(endian + "II", read_at(cursor, 8))
                if command_size < 8 or cursor + command_size > end:
                    raise ValueError("Invalid Mach-O load command size")
                if command == 0x32:
                    if command_size < 24:
                        raise ValueError("Truncated LC_BUILD_VERSION")
                    target, min_value, sdk_value, _ = struct.unpack(endian + "4I", read_at(cursor + 8, 16))
                    if target == 1:  # PLATFORM_MACOS
                        minimum, sdk = version_string(min_value), version_string(sdk_value)
                elif command == 0x24:
                    if command_size < 16:
                        raise ValueError("Truncated LC_VERSION_MIN_MACOSX")
                    min_value, sdk_value = struct.unpack(endian + "II", read_at(cursor + 8, 8))
                    minimum, sdk = version_string(min_value), version_string(sdk_value)
                cursor += command_size
            architecture = {0x100000c: "arm64", 0x1000007: "x86_64", 12: "arm", 7: "i386"}.get(cpu, f"cpu-{cpu}")
            result.append({"architecture": architecture, "cpu_subtype": subtype,
                           "minimum_macos_declared": minimum, "sdk_declared": sdk})
        return result


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Bundle file resolves outside the supplied app")
    return path


def inspect_app(app, runtime_node=None, verify_signature=True):
    root = Path(app).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("App bundle must be a directory")
    with inside(root, "Contents/Info.plist").open("rb") as source:
        info = plistlib.load(source)
    executable_name = info.get("CFBundleExecutable")
    if not isinstance(executable_name, str) or not executable_name or "/" in executable_name:
        raise ValueError("Invalid bundle executable declaration")
    executable = inside(root, "Contents/MacOS/" + executable_name)
    report = {
        "bundle_version": info.get("CFBundleShortVersionString"),
        "bundle_build": info.get("CFBundleVersion"),
        "bundle_minimum_macos_declared": info.get("LSMinimumSystemVersion"),
        "executable_sha256": sha256(executable),
        "executable_slices": macho_slices(executable),
        "compatibility_tested": False,
        "target_app_executed": False,
    }
    expanded = inside(root, "Contents/Resources/app/dist-electron/index.js")
    packed = inside(root, "Contents/Resources/app.asar")
    report["resource_layout"] = "expanded" if expanded.is_file() else "packed" if packed.is_file() else "unknown"
    report["main_js_sha256"] = sha256(expanded) if expanded.is_file() else None
    report["asar_sha256"] = sha256(packed) if packed.is_file() else None
    if runtime_node:
        node = Path(runtime_node).expanduser().resolve(strict=True)
        report["runtime_node_slices"] = macho_slices(node)
        report["runtime_node_sha256"] = sha256(node)
    report["signature_verification"] = "not-requested" if not verify_signature else "unavailable"
    if verify_signature and platform.system() == "Darwin" and shutil.which("codesign"):
        checked = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(root)],
                                 capture_output=True, timeout=60, check=False)
        report["signature_verification"] = "passed" if checked.returncode == 0 else "failed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path, help="Your local .app bundle; never launched or modified")
    parser.add_argument("--runtime-node", type=Path, help="Optional separate Node binary to inspect, never execute")
    parser.add_argument("--skip-signature", action="store_true", help="Skip read-only macOS codesign verification")
    args = parser.parse_args()
    try:
        result = inspect_app(args.app, args.runtime_node, not args.skip_signature)
    except (OSError, ValueError, plistlib.InvalidFileException, struct.error, subprocess.TimeoutExpired):
        print(json.dumps({"ok": False, "error": "Bundle inspection failed; check the bundle structure and Mach-O inputs"}))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
