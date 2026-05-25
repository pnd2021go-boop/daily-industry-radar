# Daily Industry Radar

Daily Industry Radar 是一个 Python 3.11 静态日报项目。它通过 RSS 和 Google News RSS 抓取跨境电商、家具家居、AI、科技与消费行业的公开资讯，生成适合手机端阅读的 HTML 页面，并通过 GitHub Actions 自动发布到 GitHub Pages。

系统不依赖每天登录 Codex。Codex 只用于生成和维护代码；后续每日运行由 GitHub Actions 自动完成。

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
- `data/news_archive.csv`：历史资讯数据
- `reports/YYYY-MM-DD.md`：Markdown 备份

如果当天没有抓取到资讯，页面会显示“今日未抓取到符合条件的资讯，请检查信息源或关键词配置。”

## 固定访问链接

GitHub Pages 发布后，固定访问链接通常是：

`https://<username>.github.io/<repository>/`

本项目每天定时生成新的 `site/index.html`，因此你可以一直用同一个链接查看最新一期日报；历史日报会保留在 `site/archive/` 下。

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

项目预留 OpenAI API 调用，但不是必需项。未配置时会自动使用规则方式生成简版摘要。

配置方式：

1. 打开 GitHub 仓库 `Settings`
2. 进入 `Secrets and variables` -> `Actions`
3. 点击 `New repository secret`
4. 名称填写 `OPENAI_API_KEY`
5. 值填写你的 OpenAI API Key

可选：在 `Variables` 中添加 `OPENAI_MODEL`，默认值是 `gpt-4o-mini`。

不要把 API Key 写入代码、README、config.yaml 或任何提交文件。

## 手动触发 workflow_dispatch

打开 GitHub 仓库：

`Actions` -> `Daily News Pages` -> `Run workflow`

选择分支后点击运行。适合测试 RSS、关键词、页面样式和 Pages 发布。

## 修改定时运行时间

编辑 `.github/workflows/daily-news-pages.yml` 中的 cron。

GitHub Actions 使用 UTC 时间。例如：

- 北京时间 08:30：`30 0 * * *`
- 北京时间 09:00：`0 1 * * *`
- 北京时间 18:00：`0 10 * * *`

## 查看 GitHub Pages 链接

workflow 成功后，在以下位置查看发布链接：

- `Actions` -> 最新成功的 `Daily News Pages` run -> `deploy` job
- 或 `Settings` -> `Pages`

通常格式为：

`https://<username>.github.io/<repository>/`

## 内容边界

本项目发布为公开网页，页面内容只应包含公开资讯、公开链接和中性摘要。摘要基于标题、来源、发布时间和链接生成，不应包含公司内部策略、内部判断、敏感信息或未经证实的事实。

## 常见问题排查

### GitHub Actions 没有触发

检查 `.github/workflows/daily-news-pages.yml` 是否在默认分支；确认仓库 Actions 功能已启用。定时任务使用 UTC，且 GitHub 可能有几分钟延迟。

### GitHub Pages 没有更新

确认 `Settings -> Pages` 的 Source 是 `GitHub Actions`。检查 Actions 中 `deploy` job 是否成功。如果失败，先看 `Generate daily site` 和 `Deploy to GitHub Pages` 步骤日志。

### 抓取结果为空

检查 RSS URL 是否有效，或放宽 `config.yaml` 中的 `site.lookback_hours`。Google News RSS 可能因关键词过窄返回较少结果，可以增加更宽泛的关键词。

### OPENAI_API_KEY 未配置

这是允许的。脚本会使用规则方式生成简版摘要。若要启用 AI 摘要，请在 GitHub Actions Secrets 中配置 `OPENAI_API_KEY`。

### 页面样式异常

页面 CSS 内置在 HTML 中，不依赖外部图片或框架。若样式异常，检查 `site/index.html` 是否完整生成，并确认浏览器没有打开旧缓存页面。
