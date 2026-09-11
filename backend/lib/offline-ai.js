function cleanText(text) {
  return String(text || "")
    .replace(/\s+/g, " ")
    .trim();
}

function sentences(text) {
  return cleanText(text)
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length >= 20);
}

function titleFrom(text, fallback) {
  const words = cleanText(text).split(/\s+/).slice(0, 8);
  return words.length ? `${words.join(" ")}${words.length >= 8 ? "…" : ""}` : fallback;
}

export function offlineFallbackEnabled() {
  return !["0", "false", "no", "off"].includes(
    String(process.env.ENABLE_OFFLINE_FALLBACK ?? "true").toLowerCase()
  );
}

export function createOfflineTopics(text) {
  const source = cleanText(text);
  const parts = sentences(source);
  const count = Math.min(6, Math.max(1, Math.ceil(source.length / 900)));
  const chunkSize = Math.max(1, Math.ceil(Math.max(parts.length, count) / count));
  const topics = [];

  for (let index = 0; index < parts.length && topics.length < 6; index += chunkSize) {
    const chunk = parts.slice(index, index + chunkSize).join(" ");
    topics.push({
      title: titleFrom(chunk, `Study topic ${topics.length + 1}`),
      description: chunk.slice(0, 240),
      order: topics.length + 1,
      difficulty: "College",
    });
  }

  if (!topics.length) {
    topics.push({
      title: "Core ideas from the uploaded material",
      description: source.slice(0, 240) || "Review the uploaded material and its key ideas.",
      order: 1,
      difficulty: "College",
    });
  }

  return topics;
}

export function createOfflineLesson(topic, text) {
  const keySentences = sentences(text).slice(0, 5);
  const excerpt = cleanText(text).slice(0, 1600);
  const firstPoint =
    keySentences[0] ||
    `Review the definitions, examples, and relationships described under ${topic.title}.`;

  return {
    title: topic.title,
    introduction: `This lesson is based on the uploaded material's section about ${topic.title}.`,
    explanation: excerpt || `The uploaded material introduces ${topic.title}.`,
    realLifeExample:
      "Use the examples in the uploaded material as a template, then explain the same idea in your own words.",
    importantPoints: keySentences.length ? keySentences : [firstPoint],
    examPoints: [
      `Define or explain ${topic.title}.`,
      "Support your answer with the key relationship or example given in the material.",
    ],
    summary: firstPoint,
    difficulty: topic.difficulty || "College",
    quiz: [
      {
        question: "Which statement is directly supported by the uploaded material?",
        options: [
          firstPoint.slice(0, 180),
          "The material contains no information about this topic.",
          "The topic is unrelated to the uploaded material.",
          "None of the above.",
        ],
        answerIndex: 0,
        explanation: "The first option is taken from the uploaded material.",
      },
    ],
  };
}

export function createOfflineTutorAnswer(question, text) {
  const excerpt = cleanText(text).slice(0, 1200);
  return [
    "Offline AI mode is active because the Ollama model is not reachable.",
    `I could not generate a model-written answer to: “${cleanText(question)}”`,
    excerpt
      ? `Here is the most relevant available excerpt from your material: ${excerpt}`
      : "The uploaded material does not contain readable text for an excerpt.",
  ].join("\n\n");
}

export function createOfflineTutorLesson(question, text, sources = []) {
  const source = cleanText(text);
  const parts = sentences(source);
  const chunks = [];
  for (let index = 0; index < parts.length && chunks.length < 6; index += 3) {
    chunks.push(parts.slice(index, index + 3).join(" "));
  }
  if (!chunks.length) chunks.push(source.slice(0, 1200));

  return {
    type: "structured-lesson",
    title: titleFrom(question, "Lesson from your material"),
    overview:
      "Ollama was unavailable, so this lesson is a grounded study guide assembled from the readable text in your uploaded material.",
    learningObjectives: [
      "Identify the main ideas present in the uploaded material.",
      "Explain each idea in your own words using the source examples.",
      "Check your understanding with the quick questions below.",
    ],
    sections: chunks.map((chunk, index) => ({
      title: `Material section ${index + 1}`,
      type: "concept",
      whatItIs: chunk.split(". ")[0] || "A concept from the uploaded material.",
      whyItMatters: "This is one of the main ideas found in the selected source text.",
      simpleExplanation: chunk,
      explanation: chunk,
      analogy: "",
      example: "Rewrite this source idea as a small example in your own words.",
      stepByStep: [],
      keyPoints: [chunk],
      visual: { type: "flowchart", title: "How to study this idea", data: { nodes: ["Read", "Connect", "Practice"], edges: [["Read", "Connect"], ["Connect", "Practice"]] } },
      code: null,
      formulas: [],
      commonMistakes: ["Memorizing the words without checking what the concept means."],
      examTips: ["Use the source definition first, then add a short example."],
      quiz: [
        {
          question: "Which statement is directly supported by this material?",
          options: [chunk.slice(0, 160), "The material says nothing about this.", "This topic is unrelated.", "None of the above."],
          answerIndex: 0,
          explanation: "The first option is taken from the readable source excerpt.",
        },
      ],
    })),
    sourceSections: sources.map((sourceItem) => sourceItem.id),
    sources,
    studyPlan: ["Ask Ollama-powered follow-up questions after starting the local model."],
    question: cleanText(question),
  };
}