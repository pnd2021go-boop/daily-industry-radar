# Daily Industry Radar

Daily Industry Radar 是一个 Python 3.11 静态日报项目。它通过 RSS 和 Google News RSS 抓取公开行业资讯，并每天自动生成一个面向业务判断的「每日行业知识雷达 / 业务洞察看板」。

新版目标不是做新闻网站，也不是追求信息覆盖率，而是帮助快速判断：哪些新闻真的值得看，哪些趋势正在形成，哪些内容可以迁移到品牌营销、品类规划、跨境家具业务和 AI 工作流。

系统不依赖每天登录 Codex。Codex 只用于生成和维护代码；后续每日运行由 GitHub Actions 自动完成，并发布到 GitHub Pages。

## 固定访问链接

GitHub Pages 固定访问地址：

`https://pnd2021go-boop.github.io/daily-industry-radar/`

本项目每天定时生成新的 `site/index.html`，因此可以一直用同一个链接查看最新日报；历史日报保留在 `site/archive/` 下。

## 新版内容逻辑

日报会先抓取候选资讯、识别原始发布者，再进行来源准入、多维评分和分层，而不是直接按行业标签平铺展示。Bing News 是优先发现通道，可提供原媒体直链和摘要；Google News 作为补充。两者都不参与来源评分，页面展示和评分只使用其背后的原始媒体。

### 权威来源准入

资讯范围仍覆盖跨境电商、家具家居、AI 与科技、消费零售、品牌营销和供应链，但主推送只保留以下来源：

- 美国权威商业与科技媒体，例如 Reuters、Bloomberg、WSJ、CNBC、TechCrunch、The Verge、Wired。
- 美国行业垂直媒体，例如 Retail Dive、Modern Retail、Business of Home、Furniture Today、Home News Now、Digital Commerce 360、Supply Chain Dive。
- 全球权威媒体、头部咨询研究机构，以及 Amazon、Shopify、OpenAI、Anthropic、Google、Microsoft 等官方来源。

美国权威媒体、美国行业垂直媒体和官方来源会获得优先权。openPR、EIN、SEO 趋势稿、纯聚合站、地方性弱相关新闻和来源不明内容不会进入主页面，即使标题命中了关键词。

每条资讯会生成以下评分：

- `business_relevance_score`：业务相关性，判断是否直接关联跨境电商、家具家居、Amazon / Shopify / Wayfair / DTC、AI Agent / workflow、零售科技、供应链、品牌营销、社媒和内容电商。
- `knowledge_transfer_score`：知识迁移价值，判断是否能迁移到品类规划、产品机会识别、家具系列开发、ModernMate 品牌营销、社媒内容策略、Hawkeye / Radar / Echo 等 AI 工作流、组织流程优化和中台方法论沉淀。
- `actionability_score`：行动启发度，判断是否能形成会议讨论点、产品/设计观察点、营销实验、AI 工作流优化点、弱信号观察项或复盘趋势判断。
- `source_quality_score`：来源可信度，根据美国权威媒体、美国行业媒体、全球权威媒体、机构/官方来源和低质量来源分级。
- `source_authority_label`：页面可读的来源等级，例如“美国权威/官方”或“权威行业媒体”。
- `relevance_reason`：明确写出新闻与哪些业务方向直接相关，以及可以迁移到哪些工作场景。
- `source_context_label`：标记“正文充分”“媒体摘要”或“信息有限”。主阅读区至少要求取得媒体摘要，并会再次检查摘要是否包含标题之外的事实；只有标题的条目留在归档。

低质量 SEO 趋势稿、纯新闻聚合站、openPR、地方性弱相关门店新闻，以及仅有关键词关系但没有结构性业务价值的内容会被降权，并在需要时输出 `noise_reason`。

系统会基于上述评分计算 `total_value_score`，并把资讯分为：

- `Must Read`：今日必读，最多 3 条。
- `Worth Scanning`：值得快速浏览，最多 5 条。
- `Weak Signals`：弱信号观察池，最多 5 条。
- `Archive`：普通归档，默认折叠。

## 页面结构

新版 HTML 页面优先按「主题洞察」组织，而不是按原始标签组织：

- `Header`：Daily Industry Radar、日期、今日一句话判断、今日关键词标签。
- `情报工具栏`：全文搜索，并可按必读、快读、弱信号、美国来源和本页收藏筛选。
- `Executive Brief`：用 3-5 句话总结当天最值得关注的结构性变化。
- `Must Read`：最多 3 条重点新闻，首屏直接展示事实摘要、来源等级和具体业务相关性；业务影响、知识迁移与建议动作可展开阅读。
- `Knowledge Transfer Cards`：核心模块，把新闻转化成可迁移业务洞察，包含主题、发生了什么、为什么重要、可迁移到哪里、对 ModernMate / 品类规划 / Hawkeye / Radar / Echo / 社媒营销 的启发、一个可尝试的小动作和关联新闻。
- `Worth Scanning`：高价值但不一定需要深读的资讯。
- `Weak Signals`：暂时不能下结论但值得连续观察的信号。
- `Archive`：保留原始按标签分类新闻列表，默认折叠。

页面 CSS 和 JavaScript 均内置在 HTML 中，不依赖外部框架。移动端优先，采用高密度、克制的商业情报布局。

## 收藏与转发

每条重点资讯和归档资讯都提供以下处理入口：

- `收藏`：保存在浏览器 `localStorage`，跨日期保留；“收藏夹”可集中查看并复制收藏清单。
- `转发`：手机端优先调用系统分享面板；不支持系统分享的浏览器会复制一段包含标题、事实摘要、相关性、来源和原文链接的转发文本。
- `阅读原文`：新窗口打开权威来源原文。

收藏数据仅保存在当前浏览器，不上传服务器，也不会自动同步到其他设备。这样可以继续使用纯静态 GitHub Pages，同时避免新增账号和数据服务。

## AI 摘要字段

配置 `OPENAI_API_KEY` 后，系统会要求 AI 针对重点新闻输出结构化字段：

- `summary_zh`：120-220 字中文事实摘要，优先回答主体、动作、对象、阶段、关键数字/范围和当前结果，不复制或只翻译标题。
- `relevance_reason`：解释与跨境家具、ModernMate、品类规划、社媒营销或 AI 工作流的具体连接。
- `why_it_matters`：为什么重要。
- `business_implication`：对业务的潜在影响。
- `knowledge_transfer`：可迁移洞察。
- `suggested_action`：建议动作。
- `noise_reason`：如果被降权，说明降权原因。

GitHub Actions 会优先使用 `OPENAI_API_KEY`；未配置时，自动使用工作流自带的 `GITHUB_TOKEN` 调用 GitHub Models 生成中文事实摘要，不需要额外密钥或人工审批。只有两个 AI 通道都不可用时，脚本才使用原文摘录和规则字段兜底。页面会明确标记“AI 中文事实摘要”或“原文事实摘录”，避免混淆。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

运行后会生成：

- `site/index.html`：最新日报首页
- `site/archive/YYYY-MM-DD.html`：当天归档页面
- `site/archive/index.html`：历史日报列表
- `data/news_archive.csv`：历史资讯和评分数据
- `reports/YYYY-MM-DD.md`：Markdown 备份

如果当天没有抓取到资讯，页面会显示“今日未抓取到符合条件的资讯，请检查信息源或关键词配置。”

## 维护 config.yaml

`config.yaml` 包含三类信息源：

- `rss_sources`：直接配置 RSS 名称、URL 和默认分类。
- `google_news.keywords`：按分类配置 Google News RSS 搜索关键词，支持英文和中文。
- `bing_news`：使用同一组关键词优先发现带摘要和原媒体直链的资讯，可用 `enabled` 开关。

分类值包括：

- `cross_border_ecommerce`：跨境电商
- `furniture_home`：家具与家居
- `ai_tech`：AI 与科技
- `consumer_retail`：科技与消费
- `others`：其他观察

可以调整 `site.lookback_hours` 控制抓取最近 24 或 48 小时资讯；默认是 48 小时。

## GitHub Pages 配置

在 GitHub 仓库中打开：

`Settings` -> `Pages` -> `Build and deployment`

将 Source 设置为 `GitHub Actions`。之后 workflow 成功运行时，会自动发布 `site` 目录到 GitHub Pages。

## GitHub Actions 配置

workflow 文件位于：

`.github/workflows/daily-news-pages.yml`

它会执行：

1. checkout repo
2. setup Python 3.11
3. 恢复历史归档缓存
4. install dependencies
5. run `python main.py`
6. upload GitHub Pages artifact
7. deploy to GitHub Pages

默认定时为北京时间每天早上 8:30 自动运行，对应 UTC 00:30：

```yaml
cron: "30 0 * * *"
```

同时支持 `workflow_dispatch` 手动触发。

## 配置 OPENAI_API_KEY

配置方式：

1. 打开 GitHub 仓库 `Settings`
2. 进入 `Secrets and variables` -> `Actions`
3. 点击 `New repository secret`
4. 名称填写 `OPENAI_API_KEY`
5. 值填写你的 OpenAI API Key

可选：在 `Variables` 中添加 `OPENAI_MODEL`，默认值是 `gpt-4o-mini`。

不要把 API Key 写入代码、README、config.yaml 或任何提交文件。

## 常见问题排查

### GitHub Actions 没有触发

检查 `.github/workflows/daily-news-pages.yml` 是否在默认分支；确认仓库 Actions 功能已启用。定时任务使用 UTC，且 GitHub 可能有几分钟延迟。

### GitHub Pages 没有更新

确认 `Settings -> Pages` 的 Source 是 `GitHub Actions`。检查 Actions 中 `deploy` job 是否成功。如果失败，先看 `Generate daily site` 和 `Deploy to GitHub Pages` 步骤日志。

### 抓取结果为空

检查 RSS URL 是否有效，或放宽 `config.yaml` 中的 `site.lookback_hours`。Google News RSS 可能因关键词过窄返回较少结果，可以增加更宽泛的关键词。

脚本会跳过单个解析失败的 RSS 源，避免一个坏源导致整份日报为空。

### OPENAI_API_KEY 未配置

这是允许的。GitHub Actions 会自动使用 `GITHUB_TOKEN` 和 GitHub Models 生成中文摘要；本地运行且两个令牌均不可用时，脚本才使用规则方式生成简版摘要。

### 页面样式异常

页面 CSS 内置在 HTML 中，不依赖外部图片或框架。若样式异常，检查 `site/index.html` 是否完整生成，并确认浏览器没有打开旧缓存页面。
