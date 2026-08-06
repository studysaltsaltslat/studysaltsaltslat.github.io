---
name: blog-frontmatter
description: 为本站（Astro Theme Pure 博客）新增的博客文章自动补全 Frontmatter。当用户新建了 src/content/blog 下的文章、要求配置/补齐新文章的 Frontmatter、或提到“给新文章自动生成标题/描述/标签/语言/封面图”时使用。通过 git 检测新增文章，自动生成 title、description、tags、language、publishDate，并在文章目录有图片时随机选一张作为 heroImage，随后提示用户可自行修改。
---

# Blog Frontmatter 自动配置

## 概述

检测 `src/content/blog/` 下新增（未跟踪或暂存新增）的文章，自动补全缺失的 Frontmatter 字段，并明确告知用户生成结果可自行修改。

## 步骤

1. **列出新增文章**

   运行脚本的 `--list` 模式，通过 `git status --porcelain` 找出 `src/content/blog` 下新增的文件（`??` 未跟踪 / `A` 已暂存，未跟踪文件夹会自动展开），只打印不修改：

   ```shell
   python .agents/skills/blog-frontmatter/scripts/fill_frontmatter.py --list
   ```

2. **通读全文，总结 description 与 tags**

   对每一篇新文章，**完整阅读正文内容**（不是只看第一段或做关键词匹配），然后：

   - 用一段话概括全文主旨，作为 `description`（≤160 字符）
   - 根据文章实际内容提炼 3-5 个准确的 `tags`

3. **写入 Frontmatter**

   把总结结果传给脚本，指定单篇文章（其余字段 publishDate / language / heroImage 等会自动补齐）：

   ```shell
   python .agents/skills/blog-frontmatter/scripts/fill_frontmatter.py \
     --file src/content/blog/xxx/index.md \
     --description "通读全文后总结的描述" \
     --tags 教程,自动化,写作
   ```

4. **核对输出**

   逐项核对脚本打印的结果：

   - `heroImage.src` 指向的图片文件必须真实存在于文章同目录
   - 确认总结的 description / tags 覆盖了全文内容，必要时手动修正
   - 文章内若已有 `# 标题`，脚本以该标题为准

5. **提示用户**

   将生成的字段告诉用户，并明确说明这些是自动生成的、可以自行修改。

其他参数：

- `--dry-run`：只打印将要生成的内容，不写文件
- `--all`：处理所有缺失字段的文章（不限于新增）
- `--seed N`：固定随机种子，让 heroImage 挑选可复现
- 不传 `--description` / `--tags` 时，脚本用第一段正文和关键词提取兜底

## 自动生成规则

| 字段 | 规则 |
| --- | --- |
| `title` | 优先取正文第一个 `# 标题`；否则由文件名/文件夹名转成标题；超过 60 字符截断 |
| `description` | 通读全文后用一段话总结主旨，不超过 160 字符（agent 生成后经 `--description` 传入） |
| `publishDate` | 缺失时用当天日期 `YYYY-MM-DD` |
| `tags` | 基于全文内容理解提炼 3-5 个标签（agent 生成后经 `--tags` 传入）；已有占位标签（Example/Technology）时替换 |
| `language` | 统计中文字符占比，>30% 判定为 `中文`，否则 `English` |
| `heroImage` | 文章目录存在图片（png/jpg/jpeg/gif/avif/webp）且未设置时，随机选一张，写入 `src: './图片名'` + `alt: '封面图'` |
| `draft` / `comment` | 不自动生成，保留用户已有值 |

## 本主题 Frontmatter 约束（schema）

- 必填：`title`（≤60 字符）、`description`（≤160 字符）、`publishDate`
- 可选：`updatedDate`、`tags`（自动小写去重）、`language`、`heroImage`、`draft`（默认 false）、`comment`（默认 true）
- `heroImage` 为 JSON 对象形式：

  ```yaml
  heroImage:
    src: './cover.jpg'
    alt: '封面图'
  ```

- 本地图片必须放在文章所在目录，用相对路径 `./xxx.jpg` 引用；远程图片需额外提供 `width`/`height`

## 注意事项

- 脚本保留用户已有的 Frontmatter 字段和格式，只补缺失或占位内容
- 遇到 `LocalImageUsedWrongly` 之类报错通常是 dev server 缓存问题，重启 `npm run dev` 即可
