#!/usr/bin/env python3
"""Read-only Claude CLI bridge for the codex-claude-debate Codex skill.

No Codex CLI needed: Codex Desktop runs this helper as a local shell command.
The helper invokes the real Claude Code CLI and saves each response verbatim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def resolve_executable() -> str:
    candidate = os.environ.get("CLAUDE_BIN", "claude")
    found = shutil.which(candidate)
    if found:
        return found
    path = Path(candidate).expanduser()
    if path.is_file():
        return str(path.resolve())
    raise RuntimeError(
        "Claude Code CLI not found. Run `claude --version` or set CLAUDE_BIN "
        "to the absolute executable path."
    )


def run_check(_args: argparse.Namespace) -> int:
    try:
        exe = resolve_executable()
        for cmd_args in (["--version"], ["auth", "status"]):
            proc = subprocess.run(
                [exe, *cmd_args], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=25,
                check=False,
            )
            out = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            # Status may contain account-related data: report success only.
            if cmd_args[0] == "--version":
                print(f"Claude executable: {exe}")
                print(f"Version: {out or err or '(none)'}")
            else:
                print("Authentication: " + ("OK" if proc.returncode == 0 else "NOT LOGGED IN"))
                if proc.returncode:
                    print("Try `claude auth login` in a normal terminal.")
            if proc.returncode:
                return 2
        return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"CHECK FAILED: {exc}", file=sys.stderr)
        return 2


def run_ask(args: argparse.Namespace) -> int:
    infile = Path(args.prompt_file).expanduser().resolve()
    outfile = Path(args.output_file).expanduser().resolve()
    cwd = Path(args.cwd).expanduser().resolve()
    if not infile.is_file():
        print(f"Missing prompt file: {infile}", file=sys.stderr)
        return 2
    if not cwd.is_dir():
        print(f"Missing project directory: {cwd}", file=sys.stderr)
        return 2
    prompt = infile.read_text(encoding="utf-8-sig")
    if not prompt.strip():
        print("Prompt file is empty", file=sys.stderr)
        return 2
    outfile.parent.mkdir(parents=True, exist_ok=True)

    # `-p` with piped stdin is supported by Claude Code. Disable all built-in
    # tools and MCP tools: Claude's role in this skill is a text-only critic.
    try:
        exe = resolve_executable()
        cmd = [
            exe, "-p", "Respond to the complete debate prompt supplied via standard input.",
            "--tools", "", "--disallowedTools", "mcp__*",
            "--output-format", "json",
        ]
        if args.model:
            cmd += ["--model", args.model]
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=args.timeout,
            cwd=cwd, check=False,
        )
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        outfile.with_suffix(".stderr.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print(f"CLAUDE FAILED: {exc}", file=sys.stderr)
        return 2

    rawfile = outfile.with_suffix(".raw.json")
    errfile = outfile.with_suffix(".stderr.txt")
    rawfile.write_text(proc.stdout or "", encoding="utf-8")
    errfile.write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0:
        print(f"CLAUDE FAILED: exit={proc.returncode}; see {errfile}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(proc.stdout)
    except (ValueError, TypeError) as exc:
        print(f"CLAUDE FAILED: invalid JSON ({exc}); see {rawfile}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print(f"CLAUDE FAILED: unexpected response type; see {rawfile}", file=sys.stderr)
        return 2
    if payload.get("is_error") or payload.get("subtype") == "error":
        print(f"CLAUDE FAILED: CLI reported an error; see {rawfile}", file=sys.stderr)
        return 2
    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        print(f"CLAUDE FAILED: missing result text; see {rawfile}", file=sys.stderr)
        return 2
    if re.search(r"^\s*Not logged in\b", result, re.IGNORECASE):
        print("CLAUDE FAILED: not authenticated", file=sys.stderr)
        return 2
    outfile.write_text(result.rstrip() + "\n", encoding="utf-8")
    print(f"CLAUDE OK: {outfile}")
    print(f"RAW RESPONSE: {rawfile}")
    return 0


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_hash(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser().resolve()
    if not path.is_file():
        print(f"Missing file: {path}", file=sys.stderr)
        return 2
    print(sha256_of(path))
    return 0


def run_verify(args: argparse.Namespace) -> int:
    response_path = Path(args.response_file).expanduser().resolve()
    canonical_path = Path(args.canonical_file).expanduser().resolve()
    if not response_path.is_file() or not canonical_path.is_file():
        print("Missing response or canonical file", file=sys.stderr)
        return 2
    response = response_path.read_text(encoding="utf-8-sig").strip()
    lines = response.splitlines()
    if len(lines) < 2:
        print("NO CONSENSUS: verdict header missing")
        return 3
    verdict = re.fullmatch(r"VERDICT:\s*(AGREE|REJECT)\s*", lines[0].strip(), re.I)
    claim = re.fullmatch(r"REVIEWED_SHA256:\s*([0-9a-fA-F]{64})\s*", lines[1].strip(), re.I)
    if not verdict or not claim:
        print("NO CONSENSUS: invalid verdict format or missing hash")
        return 3
    actual = sha256_of(canonical_path)
    if claim.group(1).lower() != actual:
        print(f"NO CONSENSUS: version mismatch (current sha256={actual})")
        return 3
    if verdict.group(1).upper() != "AGREE":
        print(f"NO CONSENSUS: Claude REJECTED sha256={actual}")
        return 3
    print(f"CLAUDE AGREE: matching canonical sha256={actual}")
    print("Codex must still independently agree with exactly this file.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("check", help="Check Claude CLI and login status")
    ask = subs.add_parser("ask", help="Send a prompt file to real Claude CLI")
    ask.add_argument("--prompt-file", required=True)
    ask.add_argument("--output-file", required=True)
    ask.add_argument("--cwd", default=".")
    ask.add_argument("--model", help="Optional Claude model alias, e.g. opus")
    ask.add_argument("--timeout", type=int, default=300, help="CLI timeout in seconds")
    digest = subs.add_parser("hash", help="SHA-256 of canonical solution")
    digest.add_argument("file")
    verify = subs.add_parser("verify", help="Check Claude's signoff against exact file")
    verify.add_argument("--response-file", required=True)
    verify.add_argument("--canonical-file", required=True)
    args = parser.parse_args()
    if args.command == "check":
        return run_check(args)
    if args.command == "ask":
        return run_ask(args)
    if args.command == "hash":
        return run_hash(args)
    if args.command == "verify":
        return run_verify(args)
    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
