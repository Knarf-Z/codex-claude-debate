# Codex × Claude Code 自动辩论 Skill

适用于 **Windows Codex 桌面版** 与已登录的 **Claude Code CLI**，不要求额外安装 Codex CLI。

Codex 先独立提出方案，再通过真实的本地 Claude Code CLI 获取独立提案，双方最多进行五轮批判性辩论。只有双方明确认可相同的最终 Markdown 文件，并通过 SHA-256 版本核对时，才报告 `CONSENSUS`；否则报告 `NO CONSENSUS`。

> 两个模型达成一致，不代表该方案已被验证正确。

## 安装

1. 从 GitHub 克隆或下载本仓库并解压。
2. 在仓库目录运行 `install.cmd`。
3. 脚本将 `SKILL.md` 和 `scripts/claude_bridge.py` 复制至 `%USERPROFILE%\.agents\skills\codex-claude-debate\`。
4. 在 Codex Desktop 中重新打开项目；如未出现 skill，重启 Codex。

也可以手动把上述文件放入对应目录。

确认本地 Claude Code CLI 已安装、登录：

```powershell
claude auth login
py -3 "$HOME\.agents\skills\codex-claude-debate\scripts\claude_bridge.py" check
```

## 使用示例

在 Codex Desktop 打开项目后输入：

```text
使用 $codex-claude-debate 审查这个算法/安全协议：
让 Codex 和 Claude 独立提出方案，互相找反例，最多五轮。
没有真正共识就输出 NO CONSENSUS；辩论期间不要修改项目源代码。
```

## 机制

- 两个独立初稿，避免第一轮直接互相迎合。
- 双方尽可能提出至少三个有根据的风险、反例或可证伪测试。
- 每轮都保留真实 Claude CLI 输出，记录争议、证据和修改。
- 最终方案保存在 `canonical_solution.md`，使用 SHA-256 验证所批准的具体版本。
- Claude 拒绝、CLI 失败、哈希不一致、Codex 不同意，均不能声称达成共识。
- 结果保存在当前项目的 `.agent-debates/`；敏感对话记录**不要提交到 GitHub**。

## 安全和局限

1. 发送给 Claude 的内容仍然需要先去除密钥、Token、未授权私有代码和个人信息。
2. 桥接脚本通过 CLI 参数禁用 Claude 内建工具及 MCP 工具；但 Codex 侧的“不要改代码”主要依赖 Skill 指令，**不是文件系统级强制隔离**。
3. SHA-256 只能确认双方审阅的是相同版本，不等价于密码学证明、形式化验证或可运行性测试。

默认使用标准库 Python，无额外 pip 依赖。离线测试命令：

```powershell
py -3 -m unittest discover -s tests -v
```

## 许可证

本版本尚未由仓库所有者指定开源许可证；即使仓库公开可见，也不代表自动允许复制、修改或再分发。若准备开源，请先选择并添加 `LICENSE`。
