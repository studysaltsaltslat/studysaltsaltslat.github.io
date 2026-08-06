---
name: blog-publish
description: 发布本站（Astro Theme Pure 博客）到 GitHub。当用户说“发布/推送博客”“提交并部署”“更新线上站点”等时使用：先检测工作区是否 clean、是否有未推送的提交；clean 且有未推送提交时直接 push；否则先 npm run build 确保无错误，再总结 commit 信息提交，最后 push。
---

# 博客发布

## 概述

安全地把本地改动发布到远端：先检测仓库状态，按状态决定「直接推送」还是「先构建、提交、再推送」。

## 步骤

1. **检测仓库状态**

   运行脚本的 `--check` 模式，它会报告：工作区是否 clean、是否有未推送/未拉取的提交、当前分支和上游：

   ```shell
   python .agents/skills/blog-publish/scripts/publish.py --check
   ```

2. **按状态选择路径**

   - **工作区 clean 且有未推送提交**：直接推送，无需构建

     ```shell
     python .agents/skills/blog-publish/scripts/publish.py
     ```

   - **工作区有未提交更改**：先构建确保无错误，再总结提交信息、提交、推送

     ```shell
     python .agents/skills/blog-publish/scripts/publish.py --message "feat: 发布新文章"
     ```

     脚本会依次执行：`npm run build`（失败立即中止，不提交）→ `git add -A` → `git commit -m <message>` → `git push`。

   - **工作区 clean 且没有未推送提交**：报告「无需发布」即可。

3. **总结 commit 信息**

   `--message` 由 agent 根据本次改动总结生成，参考 `git diff --stat` 和具体改动内容，使用简洁的约定式前缀（`feat:` / `fix:` / `docs:` / `chore:` 等）。

4. **验证发布结果**

   推送成功后向用户确认结果；若构建失败或推送被拒绝（如落后于远端），先报告并修复，不要强行覆盖。

## 脚本参数

- `--check`：只打印状态和计划动作，不做任何修改
- `--message "..."`：提交信息（工作区有改动时必填）
- `--dry-run`：只打印将要执行的命令，不实际执行
- `--skip-build`：跳过构建步骤（不推荐）

## 注意事项

- 构建失败时脚本会中止，绝不提交未验证的改动
- 本地落后于远端（behind > 0）时会警告，推送被拒绝后先 pull/解决冲突再重试
- 首次推送（无 upstream）时脚本会用 `git push -u origin <branch>` 自动建立上游
