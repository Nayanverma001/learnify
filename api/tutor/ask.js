import connectDB from "../../backend/lib/db.js";
import Document from "../../backend/models/Document.js";
import { requireAuth } from "../../backend/lib/auth.js";
import { generateJSON } from "../../backend/lib/local-ai.js";
import {
  createOfflineTutorLesson,
  offlineFallbackEnabled,
} from "../../backend/lib/offline-ai.js";
import {
  buildTutorPrompt,
  normalizeTutorLesson,
  retrieveTeachingContext,
} from "../../backend/lib/teaching-engine.js";
import { sendError, setCors } from "../_utils.js";

export default async function handler(req, res) {
  setCors(res, req);
  if (req.method === "OPTIONS") return res.status(204).end();

  try {
    if (req.method !== "POST") return res.status(405).json({ message: "Method not allowed" });
    const { userId } = requireAuth(req);
    await connectDB();

    const { documentId, question } = req.body || {};
    if (!question?.trim()) return res.status(400).json({ message: "Question is required" });

    const doc = await Document.findOne({ _id: documentId, userId });
    if (!doc) return res.status(404).json({ message: "Material not found" });

    const context = retrieveTeachingContext(doc.extractedText, question);
    let lesson;
    let offline = false;

    try {
      const rawLesson = await generateJSON(
        buildTutorPrompt({
          documentTitle: doc.title || doc.originalFileName,
          question: question.trim(),
          context,
        })
      );
      lesson = normalizeTutorLesson(rawLesson, {
        question: question.trim(),
        sources: context.sources,
      });
      if (!lesson.sections.length) throw new Error("The model returned no teachable sections.");
    } catch (error) {
      if (!offlineFallbackEnabled()) throw error;
      offline = true;
      lesson = createOfflineTutorLesson(question, doc.extractedText, context.sources);
    }

    return res.json({
      // `answer` remains the public response key for compatibility. It is now
      // structured JSON instead of a plain text blob.
      answer: lesson,
      lesson,
      retrievedSections: context.sources,
      ...(offline
        ? {
            warning:
              "Ollama was unavailable, so a grounded offline lesson was returned. Start Ollama for richer explanations and visuals.",
          }
        : {}),
    });
  } catch (error) {
    return sendError(res, error);
  }
}