const STOP_WORDS = new Set(
  "the a an and or of to in on for with from is are was were be this that it as by at into about how what why when where which whole explain teach material pdf".split(
    " "
  )
);

function clean(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

function sentenceChunks(text, maxChars = 4200) {
  const normalized = String(text || "")
    .replace(/\r/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  const paragraphs = normalized
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);

  const units = paragraphs.flatMap((paragraph) => {
    if (paragraph.length <= maxChars) return [paragraph];
    return paragraph
      .split(/(?<=[.!?])\s+/)
      .reduce((groups, sentence) => {
        const current = groups[groups.length - 1] || "";
        if (current && `${current} ${sentence}`.length <= maxChars) {
          groups[groups.length - 1] = `${current} ${sentence}`;
        } else {
          groups.push(sentence);
        }
        return groups;
      }, []);
  });

  return units.reduce((chunks, unit) => {
    const current = chunks[chunks.length - 1];
    if (current && `${current.text}\n${unit}`.length <= maxChars) {
      current.text = `${current.text}\n${unit}`;
    } else {
      chunks.push({ text: unit });
    }
    return chunks;
  }, []);
}

function titleForChunk(text, index) {
  const firstLine = String(text)
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line.length >= 4 && line.length <= 100);
  if (firstLine && !/[.!?]$/.test(firstLine)) return firstLine;
  const firstSentence = clean(text).split(/(?<=[.!?])\s+/)[0];
  return firstSentence
    ? firstSentence.slice(0, 84) + (firstSentence.length > 84 ? "…" : "")
    : `Material section ${index + 1}`;
}

function keywords(text) {
  return clean(text)
    .toLowerCase()
    .split(/[^a-z0-9_+#-]+/)
    .filter((word) => word.length > 2 && !STOP_WORDS.has(word));
}

export function buildTeachingChunks(text) {
  return sentenceChunks(text).map((chunk, index) => ({
    id: index + 1,
    title: titleForChunk(chunk.text, index),
    text: chunk.text,
  }));
}

function isBroadQuestion(question) {
  return /\b(whole|entire|all|everything|pdf|document|material|summar|overview|teach|chapter|notes)\b/i.test(
    question
  );
}

export function retrieveTeachingContext(text, question) {
  const chunks = buildTeachingChunks(text);
  const queryWords = keywords(question);
  const scored = chunks
    .map((chunk) => {
      const haystack = `${chunk.title} ${chunk.text}`.toLowerCase();
      const score = queryWords.reduce(
        (total, word) => total + (haystack.includes(word) ? 1 : 0),
        0
      );
      return { chunk, score };
    })
    .sort((a, b) => b.score - a.score || a.chunk.id - b.chunk.id);

  const limit = isBroadQuestion(question) ? 9 : 6;
  let selected;
  if (isBroadQuestion(question)) {
    // Sample across the document so a long PDF is not represented only by
    // its first page.
    const step = Math.max(1, Math.ceil(chunks.length / limit));
    selected = chunks.filter((_, index) => index % step === 0).slice(0, limit);
    if (chunks.length && !selected.some((item) => item.id === chunks[0].id)) {
      selected.unshift(chunks[0]);
    }
    selected = selected.slice(0, limit);
  } else {
    selected = scored
      .filter(({ score }) => score > 0)
      .slice(0, limit)
      .map(({ chunk }) => chunk);
    if (!selected.length) selected = chunks.slice(0, limit);
  }

  return {
    totalChunks: chunks.length,
    chunks: selected,
    sources: selected.map((chunk) => ({
      id: chunk.id,
      title: chunk.title,
      excerpt: clean(chunk.text).slice(0, 220),
    })),
  };
}

export function buildTutorPrompt({ documentTitle, question, context }) {
  const sourceText = context.chunks
    .map(
      (chunk) =>
        `SOURCE SECTION ${chunk.id}: ${chunk.title}\n${chunk.text.slice(0, 4200)}`
    )
    .join("\n\n");

  return `You are Learnify, a patient and rigorous college teacher. Teach the student, do not merely summarize.

Document: ${documentTitle || "Uploaded study material"}
Student request: ${question}

Use only the supplied source sections for factual claims. If something is not present, say that it is not established by the material. You may use a clearly labelled everyday analogy to make a supported concept easier, but do not invent document facts.

Return a complete lesson as JSON with exactly this high-level shape:
{
  "title": "lesson title",
  "overview": "2-4 sentence overview",
  "learningObjectives": ["what the student will be able to do"],
  "sections": [
    {
      "title": "concept title",
      "type": "concept|algorithm|definition|comparison|example",
      "whatItIs": "precise definition",
      "whyItMatters": "why the student needs it",
      "simpleExplanation": "beginner-friendly explanation",
      "explanation": "teacher-style detailed explanation",
      "analogy": "real-world analogy, or empty string if not useful",
      "example": "worked or concrete example",
      "stepByStep": ["ordered steps when applicable"],
      "keyPoints": ["important points"],
      "visual": {
        "type": "linked-list|stack|queue|tree|graph|array|memory|binary|flowchart|bar-chart|line-chart|scatter-plot|timeline|concept-map|comparison-table|none",
        "title": "visual title",
        "data": {}
      },
      "code": {"language": "javascript|python|cpp|java|text", "content": "" },
      "formulas": ["formula or complexity, if relevant"],
      "commonMistakes": ["mistakes students make"],
      "examTips": ["exam-focused advice"],
      "quiz": [
        {"question": "...", "options": ["...", "...", "...", "..."], "answerIndex": 0, "explanation": "..."}
      ]
    }
  ],
  "sourceSections": [1, 2],
  "studyPlan": ["next action"]
}

Teaching rules:
- For a broad request, cover the major concepts in a logical order with 3-8 sections.
- For each major concept, explain what it is, why it matters, a simple explanation, an example, and a quick check.
- Use visuals whenever the concept benefits from one. Visual data must be deterministic and small enough for a browser renderer. Do not return image URLs.
- For a linked list use data like {"nodes":["HEAD","10","20","30","NULL"],"connections":[["HEAD","10"],["10","20"],["20","30"],["30","NULL"]]}.
- For a flowchart use {"nodes":[{"id":"1","label":"Start"},{"id":"2","label":"Process"}],"edges":[["1","2"]]}.
- For a chart use labels and numeric values. For a comparison table use {"columns":["..."],"rows":[["...","..."]]}.
- Never put markdown fences around JSON. Keep each field useful; do not fill fields with generic filler.

SOURCE MATERIAL:
${sourceText}`;
}

function safeArray(value, fallback = []) {
  return Array.isArray(value) ? value.filter((item) => item !== null && item !== undefined) : fallback;
}

function safeString(value, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

function normalizeVisual(visual) {
  if (!visual || typeof visual !== "object") return { type: "none", title: "", data: {} };
  const allowed = new Set([
    "linked-list",
    "stack",
    "queue",
    "tree",
    "graph",
    "array",
    "memory",
    "binary",
    "flowchart",
    "bar-chart",
    "line-chart",
    "scatter-plot",
    "timeline",
    "concept-map",
    "comparison-table",
    "none",
  ]);
  return {
    type: allowed.has(visual.type) ? visual.type : "none",
    title: safeString(visual.title, "Visual explanation"),
    data: visual.data && typeof visual.data === "object" ? visual.data : {},
  };
}

export function normalizeTutorLesson(value, { question, sources = [] } = {}) {
  const input = value && typeof value === "object" ? value : {};
  const sections = safeArray(input.sections)
    .slice(0, 8)
    .map((section, index) => ({
      title: safeString(section?.title, `Concept ${index + 1}`),
      type: safeString(section?.type, "concept"),
      whatItIs: safeString(section?.whatItIs),
      whyItMatters: safeString(section?.whyItMatters),
      simpleExplanation: safeString(section?.simpleExplanation, safeString(section?.explanation)),
      explanation: safeString(section?.explanation, safeString(section?.simpleExplanation)),
      analogy: safeString(section?.analogy),
      example: safeString(section?.example),
      stepByStep: safeArray(section?.stepByStep).map((item) => String(item)),
      keyPoints: safeArray(section?.keyPoints).map((item) => String(item)).slice(0, 10),
      visual: normalizeVisual(section?.visual),
      code:
        section?.code && typeof section.code === "object"
          ? {
              language: safeString(section.code.language, "text"),
              content: safeString(section.code.content),
            }
          : null,
      formulas: safeArray(section?.formulas).map((item) => String(item)),
      commonMistakes: safeArray(section?.commonMistakes).map((item) => String(item)),
      examTips: safeArray(section?.examTips).map((item) => String(item)),
      quiz: safeArray(section?.quiz)
        .slice(0, 3)
        .map((item) => ({
          question: safeString(item?.question),
          options: safeArray(item?.options).map((option) => String(option)).slice(0, 4),
          answerIndex: Number.isInteger(item?.answerIndex) ? item.answerIndex : 0,
          explanation: safeString(item?.explanation),
        }))
        .filter((item) => item.question),
    }))
    .filter((section) => section.title || section.explanation);

  return {
    type: "structured-lesson",
    title: safeString(input.title, "Learnify lesson"),
    overview: safeString(input.overview, "This lesson is grounded in your uploaded material."),
    learningObjectives: safeArray(input.learningObjectives).map((item) => String(item)).slice(0, 8),
    sections,
    sourceSections: safeArray(input.sourceSections).map(Number).filter(Number.isFinite),
    sources,
    studyPlan: safeArray(input.studyPlan).map((item) => String(item)).slice(0, 6),
    question: safeString(question),
  };
}