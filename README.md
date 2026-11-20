# Codex × Claude Code Debate

An agent skill for **Codex Desktop** that orchestrates a real, recorded, adversarial design review with **Claude Code CLI**.

Codex drafts its own proposal first. Claude independently proposes a solution using a separate local CLI invocation. The two agents exchange critiques for up to five rounds. A final `CONSENSUS` is reported **only when both explicitly approve the same canonical document**, identified by its SHA-256 digest.

**This is not a formal verification system.** Agreement is evidence of review, not proof of correctness.

[中文说明](README_zh.md)

## Features

- **Real Claude Code CLI:** uses `claude -p`, not fabricated model responses.
- **Independent opening proposals:** Codex writes its proposal before it receives Claude's.
- **Adversarial rounds:** each agent critiques the other's assumptions, failure modes, and testability.
- **Recorded review:** intermediate prompts, responses, CLI errors, and verdicts live in `.agent-debates/`.
- **Exact-document signoff:** Claude's `AGREE` must be accompanied by a matching canonical SHA-256 digest, and Codex must independently agree.
- **Fail closed:** CLI errors, unverifiable versions, or unresolved objections produce `NO CONSENSUS`.
- **No Codex CLI requirement:** Codex Desktop is the orchestrator; a Python helper invokes the Claude CLI.

## Requirements

- Windows with Codex Desktop able to run local commands.
- Claude Code CLI installed and authenticated (`claude auth login`).
- Python 3.9+ (`py -3` or `python3`).
- Local execution permissions for the assistant to run the helper.

The skill is designed around a Windows installation path. Other platforms can install it manually if they adapt paths and invocation commands.

## Installation on Windows

1. Clone or download this repository.
2. Run `install.cmd` from the checked-out or extracted directory.
3. Restart Codex Desktop, if needed.

The installer copies the skill to:

```text
%USERPROFILE%\.agents\skills\codex-claude-debate\
```

Manual installation is also possible: copy `SKILL.md` and `scripts/claude_bridge.py` into that same folder.

Check your Claude CLI connection:

```powershell
py -3 "$HOME\.agents\skills\codex-claude-debate\scripts\claude_bridge.py" check
```

## Usage

In your project in Codex Desktop:

```text
Use $codex-claude-debate to review this protocol design.
Have Codex and Claude write independent proposals, challenge each other
for at most five rounds, and report NO CONSENSUS if objections remain.
Do not change project source code during the debate.
```

Or in Chinese:

```text
使用 $codex-claude-debate，让 Codex 和 Claude 独立设计这个方案并互相找反例。
最多五轮；没有真正共识就输出 NO CONSENSUS；辩论期间不要修改项目代码。
```

## Files

```text
.
├── SKILL.md                    # Agent skill instructions
├── scripts/
│   └── claude_bridge.py        # Local Claude CLI interface and SHA-256 verifier
├── install.cmd                 # Windows user-level skill installer
├── README.md                   # English documentation
├── README_zh.md                # Chinese documentation
├── tests/
│   └── test_claude_bridge.py   # Offline verifier tests
├── .github/workflows/test.yml  # CI smoke tests
└── .gitignore
```

Debate artifacts are produced inside **the project you are reviewing**, not this repository, under `.agent-debates/<task-id>/`. They are excluded from Git by the included `.gitignore` if it is copied to that project.

## Security and limitations

1. **Sensitive input:** Claude receives whatever context Codex sends. Never send credentials, unpublished source, personal information, or proprietary data without authorization. Debate transcripts may contain those details; do not commit them.
2. **Read-only is scoped:** `claude_bridge.py` invokes the CLI with no built-in tools and disallows MCP tools. The *Codex* side is instructed not to edit project code, but the skill text is not a sandbox or an enforceable filesystem restriction.
3. **Signoff is not correctness:** matching hashes identify a shared text version; they do not validate the claims within it. Run tests, audits, and formal proofs separately.

This repository contains **no API keys or login tokens**. It relies on the user's existing local Claude Code session. CLI compatibility and authentication should be verified on each host.

## Tests

The offline tests do **not** call Claude or Codex. Run:

```powershell
py -3 -m unittest discover -s tests -v
```

An end-to-end test requires authenticated `claude` and Codex Desktop on your own computer.

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 Knarf-Z. You may use, modify, distribute, and commercially use the code under the terms of the license; retain the copyright and license notices.
