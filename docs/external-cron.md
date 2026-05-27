# External Cron Trigger

This project should not rely only on GitHub Actions `schedule`, because scheduled runs can be delayed or missed. Use an external scheduler to call GitHub's `workflow_dispatch` API every morning.

## Recommended Setup

Keep the existing GitHub Actions schedule as a backup, and add an external cron job as the primary trigger.

Recommended Beijing time triggers:

- 08:35
- 09:05 backup retry
- 09:35 final backup retry

All three triggers can call the same GitHub API endpoint. Re-running the same day is acceptable because the site always overwrites `site/index.html` with the latest daily report and keeps the dated archive page.

## GitHub Token

Create a fine-grained personal access token:

1. GitHub -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens.
2. Repository access: only `pnd2021go-boop/daily-industry-radar`.
3. Repository permissions: `Actions: Read and write`.
4. Expiration: choose a date you can maintain, or set a long expiration if acceptable.
5. Store this token only in the external scheduler's secret storage. Do not commit it to this repository.

GitHub's workflow dispatch API requires the workflow to support `workflow_dispatch`, which this project already does.

## API Request

Use this HTTP request:

```bash
curl -L -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <GITHUB_TOKEN>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/pnd2021go-boop/daily-industry-radar/actions/workflows/daily-news-pages.yml/dispatches \
  -d '{"ref":"main"}'
```

Expected response:

- `204 No Content`: trigger accepted.
- `401` or `403`: token or permission is wrong.
- `404`: repository, workflow filename, or token repository access is wrong.

## cron-job.org Setup

1. Create a cron-job.org account.
2. Create a new cron job.
3. URL:
   `https://api.github.com/repos/pnd2021go-boop/daily-industry-radar/actions/workflows/daily-news-pages.yml/dispatches`
4. Method: `POST`.
5. Timezone: `Asia/Shanghai`.
6. Schedule:
   - `08:35` daily
   - create two more jobs for `09:05` and `09:35`
7. Headers:
   - `Accept: application/vnd.github+json`
   - `Authorization: Bearer <GITHUB_TOKEN>`
   - `X-GitHub-Api-Version: 2022-11-28`
   - `Content-Type: application/json`
8. Body:

```json
{"ref":"main"}
```

## Cloudflare Workers Cron Setup

Use `docs/cloudflare-worker-trigger.js` as the Worker script.

Configure Worker secrets:

```bash
wrangler secret put GITHUB_TOKEN
```

Configure Worker variables:

```toml
[vars]
GITHUB_OWNER = "pnd2021go-boop"
GITHUB_REPO = "daily-industry-radar"
GITHUB_WORKFLOW = "daily-news-pages.yml"
GITHUB_REF = "main"
```

Recommended `wrangler.toml` cron triggers are UTC:

```toml
[triggers]
crons = ["35 0 * * *", "5 1 * * *", "35 1 * * *"]
```

These correspond to Beijing time 08:35, 09:05, and 09:35.

## Verification

After the external cron runs:

1. Open GitHub -> Actions -> Daily News Pages.
2. Confirm a `workflow_dispatch` run was created.
3. Confirm the run completed successfully.
4. Open the Pages URL:
   `https://pnd2021go-boop.github.io/daily-industry-radar/`
5. Confirm the page date is today.
