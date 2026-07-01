# Daily Industry Radar

Daily Industry Radar 是一个 Python 3.11 静态日报项目。它通过 RSS 和 Google News RSS 抓取公开行业资讯，并每天自动生成一个面向业务判断的「每日行业知识雷达 / 业务洞察看板」。

新版目标不是做新闻网站，也不是追求信息覆盖率，而是帮助快速判断：哪些新闻真的值得看，哪些趋势正在形成，哪些内容可以迁移到品牌营销、品类规划、跨境家具业务和 AI 工作流。

系统不依赖每天登录 Codex。Codex 只用于生成和维护代码；后续每日运行由 GitHub Actions 自动完成，并发布到 GitHub Pages。

## 固定访问链接

GitHub Pages 固定访问地址：

`https://pnd2021go-boop.github.io/daily-industry-radar/`

本项目每天定时生成新的 `site/index.html`，因此可以一直用同一个链接查看最新日报；历史日报保留在 `site/archive/` 下。

## 新版内容逻辑

日报会先抓取候选资讯，再进行多维评分和分层，而不是直接按行业标签平铺展示。

每条资讯会生成以下评分：

- `business_relevance_score`：业务相关性，判断是否直接关联跨境电商、家具家居、Amazon / Shopify / Wayfair / DTC、AI Agent / workflow、零售科技、供应链、品牌营销、社媒和内容电商。
- `knowledge_transfer_score`：知识迁移价值，判断是否能迁移到品类规划、产品机会识别、家具系列开发、ModernMate 品牌营销、社媒内容策略、Hawkeye / Radar / Echo 等 AI 工作流、组织流程优化和中台方法论沉淀。
- `actionability_score`：行动启发度，判断是否能形成会议讨论点、产品/设计观察点、营销实验、AI 工作流优化点、弱信号观察项或复盘趋势判断。
- `source_quality_score`：来源可信度，根据来源质量加权。TechCrunch、The Verge、Retail Dive、Modern Retail、Business of Home、Furniture Today、Home Furnishings News、Shopify、Amazon、OpenAI、Anthropic、Google、Microsoft、Oracle、McKinsey、Bain、Deloitte、Gartner、Reuters、Bloomberg、WSJ、CNBC 等来源会获得更高权重。

低质量 SEO 趋势稿、纯新闻聚合站、openPR、地方性弱相关门店新闻，以及仅有关键词关系但没有结构性业务价值的内容会被降权，并在需要时输出 `noise_reason`。

系统会基于上述评分计算 `total_value_score`，并把资讯分为：

- `Must Read`：今日必读，最多 3 条。
- `Worth Scanning`：值得快速浏览，最多 5 条。
- `Weak Signals`：弱信号观察池，最多 5 条。
- `Archive`：普通归档，默认折叠。

## 页面结构

新版 HTML 页面优先按「主题洞察」组织，而不是按原始标签组织：

- `Header`：Daily Industry Radar、日期、今日一句话判断、今日关键词标签。
- `Executive Brief`：用 3-5 句话总结当天最值得关注的结构性变化。
- `Must Read`：最多 3 条重点新闻，展示标题、来源、原始标签、可信度、业务相关性、知识迁移价值、行动启发度、摘要、为什么重要、业务启发和原文链接。
- `Knowledge Transfer Cards`：核心模块，把新闻转化成可迁移业务洞察，包含主题、发生了什么、为什么重要、可迁移到哪里、对 ModernMate / 品类规划 / Hawkeye / Radar / Echo / 社媒营销 的启发、一个可尝试的小动作和关联新闻。
- `Worth Scanning`：高价值但不一定需要深读的资讯。
- `Weak Signals`：暂时不能下结论但值得连续观察的信号。
- `Archive`：保留原始按标签分类新闻列表，默认折叠。

页面 CSS 内置在 HTML 中，移动端优先，采用克制的卡片式布局，重点内容在首屏呈现。

## AI 摘要字段

配置 `OPENAI_API_KEY` 后，系统会要求 AI 针对重点新闻输出结构化字段：

- `summary_zh`：中文摘要，不复制标题。
- `why_it_matters`：为什么重要。
- `business_implication`：对业务的潜在影响。
- `knowledge_transfer`：可迁移洞察。
- `suggested_action`：建议动作。
- `noise_reason`：如果被降权，说明降权原因。

未配置 `OPENAI_API_KEY` 时，脚本会使用规则方式生成简版摘要和洞察字段，保证日报仍可自动运行。

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

`config.yaml` 包含两类信息源：

- `rss_sources`：直接配置 RSS 名称、URL 和默认分类。
- `google_news.keywords`：按分类配置 Google News RSS 搜索关键词，支持英文和中文。

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

这是允许的。脚本会使用规则方式生成简版摘要。若要启用 AI 摘要，请在 GitHub Actions Secrets 中配置 `OPENAI_API_KEY`。

### 页面样式异常

页面 CSS 内置在 HTML 中，不依赖外部图片或框架。若样式异常，检查 `site/index.html` 是否完整生成，并确认浏览器没有打开旧缓存页面。
