export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(triggerDailyNews(env));
  },

  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Use POST to trigger the workflow.", { status: 405 });
    }

    const result = await triggerDailyNews(env);
    return new Response(JSON.stringify(result), {
      status: result.ok ? 200 : 500,
      headers: { "content-type": "application/json" },
    });
  },
};

async function triggerDailyNews(env) {
  const owner = env.GITHUB_OWNER || "pnd2021go-boop";
  const repo = env.GITHUB_REPO || "daily-industry-radar";
  const workflow = env.GITHUB_WORKFLOW || "daily-news-pages.yml";
  const ref = env.GITHUB_REF || "main";
  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "accept": "application/vnd.github+json",
      "authorization": `Bearer ${env.GITHUB_TOKEN}`,
      "content-type": "application/json",
      "user-agent": "daily-industry-radar-external-cron",
      "x-github-api-version": "2022-11-28",
    },
    body: JSON.stringify({ ref }),
  });

  return {
    ok: response.status === 204,
    status: response.status,
    statusText: response.statusText,
    workflow,
    ref,
  };
}
