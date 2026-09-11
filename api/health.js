import { setCors } from "./_utils.js";

export default function handler(req, res) {
  setCors(res, req);
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") {
    return res.status(405).json({ success: false, message: "Method not allowed" });
  }

  return res.status(200).json({
    success: true,
    service: "learnify-ai-api",
    databaseConfigured: Boolean(process.env.MONGODB_URI),
    ollamaConfigured: Boolean(process.env.OLLAMA_HOST),
    offlineFallbackEnabled:
      !["0", "false", "no", "off"].includes(
        String(process.env.ENABLE_OFFLINE_FALLBACK ?? "true").toLowerCase()
      ),
  });
}