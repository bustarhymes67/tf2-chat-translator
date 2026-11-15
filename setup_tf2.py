"""One-time setup: sets TF2's launch options in Steam so the translator can read chat
(-condebug) and, for the chat modes, say translations over RCON (-usercon and a random
password that's kept only in config.json on this PC).

Steam must be fully closed: it rewrites its config file when it exits. A backup is kept.
"""

import glob
import os
import re
import secrets
import shutil
import subprocess
import sys
import time

import translator

STEAM_USERDATA = r"C:\Program Files (x86)\Steam\userdata"
APP_PATH = ["userlocalconfigstore", "software", "valve", "steam", "apps", "440"]

# Flags this tool manages, with how many arguments each one takes.
OUR_FLAGS = {"-condebug": 0, "-usercon": 0, "+ip": 1, "+rcon_password": 1, "+hostport": 1, "+net_start": 0}

KEY_LINE_RE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*$')
KEY_VALUE_RE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)*)"(\s+)"((?:[^"\\]|\\.)*)"\s*$')


def steam_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"],
                         capture_output=True, text=True).stdout
    return "steam.exe" in out.lower()


def merge_options(existing, ours):
    """Keeps the user's own launch options, replacing only the ones we manage."""
    tokens, kept, i = existing.split(), [], 0
    while i < len(tokens):
        if tokens[i].lower() in OUR_FLAGS:
            i += 1 + OUR_FLAGS[tokens[i].lower()]
        else:
            kept.append(tokens[i])
            i += 1
    return " ".join(kept + [ours])


def set_launch_options(path, ours):
    """Edits TF2's LaunchOptions in a localconfig.vdf. Returns (old, new)."""
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    eol = "\r\n" if "\r\n" in text else "\n"  # keep Steam's own line endings
    lines = text.split(eol)
    stack, pending, old = [], None, None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "{":
            stack.append(pending)
        elif stripped == "}":
            if stack == APP_PATH:
                # Block ended without LaunchOptions: add it.
                new = merge_options("", ours)
                lines.insert(i, "\t" * len(stack) + f'"LaunchOptions"\t\t"{new}"')
                break
            stack.pop()
        elif m := KEY_VALUE_RE.match(line):
            if stack == APP_PATH and m.group(2).lower() == "launchoptions":
                old = m.group(4)
                new = merge_options(old, ours)
                lines[i] = f'{m.group(1)}"{m.group(2)}"{m.group(3)}"{new}"'
                break
        elif m := KEY_LINE_RE.match(line):
            pending = m.group(1).lower()
    else:
        raise LookupError("TF2's entry wasn't found in Steam's config. Launch TF2 once, then retry.")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(lines))
    return old, new


def launch_options(cfg):
    return (f"-condebug -usercon +ip 0.0.0.0 +rcon_password {cfg['rcon_password']} "
            f"+hostport {cfg['rcon_port']} +net_start")


def config_files():
    return glob.glob(os.path.join(STEAM_USERDATA, "*", "config", "localconfig.vdf"))


def main():
    cfg = translator.load_config()
    if not cfg["rcon_password"]:
        cfg["rcon_password"] = secrets.token_hex(8)
        translator.save_config(cfg)
    if steam_running():
        print("Steam is running, so TF2's launch options can't be changed yet.")
        print("Close TF2, quit Steam completely (Steam menu > Exit), then run Setup again.")
        return 1
    files = config_files()
    if not files:
        print("Steam's config wasn't found. Is Steam installed in C:\\Program Files (x86)\\Steam?")
        return 1
    for path in files:
        shutil.copy2(path, f"{path}.backup-{time.strftime('%Y%m%d-%H%M%S')}")
        try:
            old, _ = set_launch_options(path, launch_options(cfg))
        except LookupError:
            continue  # an account on this PC that never launched TF2
        old = re.sub(r"(\+rcon_password )\S+", r"\1<hidden>", old or "empty")
        print(f"TF2 launch options updated (were: {old}).")
    print("\nDone. Start Steam and TF2, then pick a mode in Start Translator.bat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
