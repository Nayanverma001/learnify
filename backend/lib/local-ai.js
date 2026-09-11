// Talks to an Ollama server over HTTP instead of spawning the `ollama`
// CLI as a child process. Vercel serverless functions run in short-lived,
// stateless containers with no Ollama binary installed and no way to run
// a local LLM in-process, so `spawn("ollama", ...)` always fails there
// ("Could not start Ollama"). Ollama has always exposed this same
// functionality over HTTP (this is what the CLI itself calls under the
// hood), so pointing at a remote Ollama instance via OLLAMA_HOST fixes
// this without changing anything about how you run Ollama locally.
//
// Local dev: leave OLLAMA_HOST unset, run `ollama serve` (or just
// `ollama run <model>` once, which starts the server for you), and it
// defaults to http://127.0.0.1:11434 exactly like before.
//
// Production on Vercel: install Ollama on a small always-on VPS (a $5-6/mo
// box with 8-16GB RAM is enough for a 7B/8B quantized model), run
// `ollama serve`, expose port 11434 (behind a firewall / reverse proxy
// with auth if it's public), and set OLLAMA_HOST=http://YOUR_SERVER_IP:11434
// as a Vercel environment variable.

const OLLAMA_HOST = (process.env.OLLAMA_HOST || "http://127.0.0.1:11434").replace(/\/+$/, "");
// Support both names so existing .env files keep working while new
// deployments can use the clearer OLLAMA_MODEL name.
const MODEL =
  process.env.OLLAMA_MODEL || process.env.LOCAL_LLM_MODEL || "qwen2.5:7b";
const TIMEOUT_MS = Number(process.env.LOCAL_LLM_TIMEOUT_MS || 300000);

async function callOllama(prompt) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let response;
  try {
    response = await fetch(`${OLLAMA_HOST}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: MODEL,
        prompt,
        stream: false,
      }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(`Local LLM timed out after ${TIMEOUT_MS / 1000}s`);
    }
    throw new Error(
      `Could not reach Ollama at ${OLLAMA_HOST}. Make sure Ollama is running there and OLLAMA_HOST is set correctly. ${err.message}`
    );
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    if (response.status === 404) {
      throw new Error(
        `Ollama model "${MODEL}" is not available on ${OLLAMA_HOST}. Run "ollama pull ${MODEL}" on that server first.`
      );
    }
    throw new Error(`Ollama request failed (${response.status}). ${body.slice(0, 500)}`);
  }

  const data = await response.json();
  return (data.response || "").trim();
}

function stripCodeFences(text) {
  return text.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();
}

export async function generateText(prompt) {
  return callOllama(prompt);
}

export async function generateJSON(prompt) {
  const output = await callOllama(
    `${prompt}\n\nIMPORTANT: Return ONLY valid JSON. No markdown fences, no commentary.`
  );
  const cleaned = stripCodeFences(output);
  try {
    return JSON.parse(cleaned);
  } catch {
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return JSON.parse(cleaned.slice(start, end + 1));
    }
    throw new Error(`Local model returned invalid JSON: ${cleaned.slice(0, 500)}`);
  }
}
