import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODEL = os.environ.get("OLLAMA_MODEL") or os.environ.get("LOCAL_LLM_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
TIMEOUT = int(os.environ.get("LOCAL_LLM_TIMEOUT_SECONDS", "300"))


def _offline_fallback_enabled():
    return os.environ.get("ENABLE_OFFLINE_FALLBACK", "true").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _generate_with_ollama(prompt):
    request = Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")[:500]
        if error.code == 404:
            raise RuntimeError(
                f'Ollama model "{MODEL}" is not available on {OLLAMA_HOST}. '
                f"Run `ollama pull {MODEL}` on that server first."
            ) from error
        raise RuntimeError(f"Ollama request failed ({error.code}): {body}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_HOST}. Set OLLAMA_HOST to a reachable "
            f"Ollama server or install/start Ollama locally. {error}"
        ) from error

    result = str(payload.get("response", "")).strip()
    if not result:
        raise RuntimeError("Local LLM returned an empty response.")
    return result


def _parse_json(text):
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        start_arr, end_arr = cleaned.find("["), cleaned.rfind("]")
        if start_arr >= 0 and end_arr > start_arr:
            return json.loads(cleaned[start_arr : end_arr + 1])
        raise


def _clean_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _sentences(text):
    clean = _clean_text(text)
    if not clean:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if len(s.strip()) > 15]


def _detect_visual_type(text):
    lower = text.lower()
    if any(k in lower for k in ["linked list", "pointer", "node", "memory address"]):
        return {
            "type": "linked-list",
            "title": "Memory Node Chain and Pointers",
            "data": {"nodes": ["HEAD", "Node 1", "Node 2", "Node 3", "NULL"]},
        }
    if "stack" in lower:
        return {"type": "stack", "title": "LIFO Stack Layout", "data": {"nodes": ["TOP", "Item C", "Item B", "Item A"]}}
    if "queue" in lower:
        return {"type": "queue", "title": "FIFO Queue Structure", "data": {"nodes": ["FRONT", "Task 1", "Task 2", "REAR"]}}
    if any(k in lower for k in ["time complexity", "performance", "benchmark", "comparison", "rate", "latency", "percentage", "growth", "cost"]):
        return {
            "type": "bar-chart",
            "title": "Complexity and Operation Growth",
            "data": {"labels": ["N=10", "N=100", "N=1K", "N=10K", "N=100K"], "values": [3, 7, 10, 14, 17]},
        }
    if any(k in lower for k in ["tree", "binary tree", "hierarchy", "parent", "child", "bst"]):
        return {
            "type": "tree",
            "title": "Hierarchical Tree Structure",
            "data": {"nodes": [{"label": "Root Node", "children": ["Left Child", "Right Child"]}]},
        }
    if any(k in lower for k in ["difference", "vs", "contrast", "properties", "types"]):
        return {
            "type": "comparison-table",
            "title": "Feature and Property Matrix",
            "data": {
                "columns": ["Parameter", "Approach A", "Approach B"],
                "rows": [
                    ["Time Complexity", "O(1) to O(n)", "O(log n)"],
                    ["Space Overhead", "Minimal", "Auxiliary pointers"],
                    ["Best Use Case", "Small / streaming", "Large static index"],
                ],
            },
        }
    return {
        "type": "flowchart",
        "title": "Step-by-Step Algorithmic Process",
        "data": {
            "nodes": [
                {"label": "1. Input Setup"},
                {"label": "2. Condition Check"},
                {"label": "3. Core Execution"},
                {"label": "4. State Update"},
                {"label": "5. Optimal Output"},
            ]
        },
    }


def _offline_masterclass_curriculum(text, options=None):
    clean = _clean_text(text)
    s_list = _sentences(clean)
    topic_title = s_list[0][:65] if s_list else "Core Study Topic"
    if "." in topic_title:
        topic_title = topic_title.split(".")[0]

    s1 = s_list[0] if len(s_list) > 0 else "This topic covers essential principles in the uploaded study notes."
    s2 = s_list[1] if len(s_list) > 1 else "Every small detail in this topic builds upon fundamental definitions."
    s3 = s_list[2] if len(s_list) > 2 else "Understanding how the steps connect ensures deep problem solving."
    s4 = s_list[3] if len(s_list) > 3 else "Practical applications showcase how these rules operate under real constraints."
    s5 = s_list[4] if len(s_list) > 4 else "Reviewing common edge cases cements theoretical mastery."

    scenes = [
        {
            "sceneNumber": 1,
            "slideType": "standard",
            "title": f"Introduction: {topic_title}",
            "narration": (
                f"Welcome to this masterclass on {topic_title}. "
                f"{s1} In this video, we will break down the entire topic in detail, "
                f"defining every core term, illustrating the inner architecture with diagrams, "
                f"walking through examples, and testing your retention with checkpoint quizzes."
            ),
            "keyPoints": [
                "Fundamental concept introduction",
                "Why this principle is critical",
                "Core roadmap for today lecture",
            ],
            "visual": _detect_visual_type(clean),
        },
        {
            "sceneNumber": 2,
            "slideType": "definition",
            "title": "Key Definitions and Core Terminology",
            "narration": (
                f"Before going deeper, we must define the precise terminology. "
                f"{s1} In formal terms, this concept establishes clear rules and constraints. "
                f"In simple words, think of it as a set of predictable operations that guarantee a reliable result. "
                f"Knowing these exact definitions prevents confusion when analyzing complex scenarios."
            ),
            "definition": s1,
            "intuition": s2,
            "whyItMatters": "Establishes the foundational boundary conditions and guarantees correctness.",
            "keyPoints": [
                "Formal mathematical or technical definition",
                "Plain-English intuitive mental model",
                "Invariant conditions that always hold true",
            ],
            "visual": {"type": "definition", "title": "Term Breakdown", "data": {}},
        },
        {
            "sceneNumber": 3,
            "slideType": "standard",
            "title": "Deep Dive: Mechanism and Execution",
            "narration": (
                f"Now let us explore the inner mechanics step by step. {s2} "
                f"{s3} Notice how each phase transitions directly into the next. "
                f"By systematically verifying preconditions at each step, we avoid errors and optimize overall performance."
            ),
            "keyPoints": [
                "Phase 1: Precondition check and input parsing",
                "Phase 2: Core processing and state transformations",
                "Phase 3: Termination criteria and output verification",
            ],
            "visual": {
                "type": "flowchart",
                "title": "Execution Pipeline",
                "data": {
                    "nodes": [
                        "Input Initialization",
                        "Validate Preconditions",
                        "Iterative Execution",
                        "Update State or Range",
                        "Return Verified Result",
                    ]
                },
            },
        },
        {
            "sceneNumber": 4,
            "slideType": "standard",
            "title": "Structural Architecture and Visual Model",
            "narration": (
                f"Let us examine the structural relationship on screen. {s3} "
                f"{s4} Connecting the theoretical rules to this visual representation allows you to visualize "
                f"how data flows and where bottlenecks might occur."
            ),
            "keyPoints": [
                "Hierarchical or sequential data flow",
                "Clear separation of concerns across components",
                "Predictable state transitions at each boundary",
            ],
            "visual": _detect_visual_type(clean),
        },
        {
            "sceneNumber": 5,
            "slideType": "quiz",
            "title": "Interactive Checkpoint Quiz",
            "narration": (
                f"Now it is time for a quick knowledge check to test your understanding. "
                f"Consider this question: Which statement best describes the fundamental behavior established by this material? "
                f"Take a second to inspect the four options on your screen. "
                f"The correct answer is Option A. As we discussed, Option A directly captures the core rule, "
                f"whereas the alternative options reflect common misconceptions."
            ),
            "quiz": {
                "question": f"Which statement is strictly true regarding {topic_title}?",
                "options": [
                    s1[:60] if len(s1) > 20 else "It guarantees deterministic behavior under sorted constraints",
                    "It operates randomly without checking input conditions",
                    "It requires unlimited exponential memory for every execution",
                    "It has no defined termination criteria or output",
                ],
                "answerIndex": 0,
                "explanation": f"Option A is directly supported by the material: {s1[:120]}. The other choices contradict basic algorithmic rules.",
            },
        },
        {
            "sceneNumber": 6,
            "slideType": "standard",
            "title": "Summary and Exam Takeaways",
            "narration": (
                f"To conclude today lecture, let us summarize the key takeaways. {s4} {s5} "
                f"Always remember the core definitions, verify your boundary conditions, and apply these principles with confidence. "
                f"Great work completing this masterclass!"
            ),
            "keyPoints": [
                "Master the core definition and technical invariants",
                "Visualize the workflow using structured diagrams",
                "Avoid common pitfalls by testing boundary cases",
            ],
            "visual": {
                "type": "flowchart",
                "title": "Mastery Checklist",
                "data": {"nodes": ["Understand Definition", "Trace Diagram", "Pass Quiz Checkpoint", "Master Topic"]},
            },
        },
    ]
    return scenes


def generate_curriculum(full_text: str, options=None):
    options = options or {}
    language = options.get("language", "English")
    level = options.get("level", "College")
    style = options.get("style", "Teacher")
    duration = options.get("duration", "5")

    clean = _clean_text(full_text)
    if not clean:
        return _offline_masterclass_curriculum("Core Educational Subject", options)

    prompt = f"""
You are an award-winning university professor and premier educational YouTube creator (like 3Blue1Brown, Khan Academy, and MIT OpenCourseWare).
Your mission: Transform the supplied study notes into an IN-DEPTH, engaging, step-by-step masterclass video curriculum.

Do NOT produce basic or superficial summaries.
Explain the topic in full depth:
1. Define every specialized term and small detail with high academic precision.
2. Provide intuitive real-world analogies (Think of it like...).
3. Explain how the mechanics work under the hood step-by-step.
4. Include deterministic diagrams/charts with real structured data.
5. Include an interactive checkpoint quiz slide with 4 options and detailed explanation.

Return ONLY a valid JSON object with this exact shape:
{{
  "topic": "Specific Subject Name",
  "scenes": [
    {{
      "sceneNumber": 1,
      "slideType": "standard",
      "title": "Clear descriptive scene title",
      "narration": "Spoken teacher narration. Introduce the big picture, why it matters, and hook the student.",
      "keyPoints": ["Point 1", "Point 2", "Point 3"],
      "visual": {{
        "type": "flowchart|tree|bar-chart|line-chart|linked-list|comparison-table|none",
        "title": "Visual Title",
        "data": {{
          "nodes": ["Step 1", "Step 2", "Step 3"],
          "labels": ["A", "B", "C"],
          "values": [10, 25, 40]
        }}
      }}
    }},
    {{
      "sceneNumber": 2,
      "slideType": "definition",
      "title": "Core Definition: [Primary Term]",
      "narration": "Deep spoken explanation defining this term, why it was invented, and how to spot it.",
      "definition": "Formal rigorous definition of the term.",
      "intuition": "Plain-English intuition or real-world mental model.",
      "whyItMatters": "Why every student needs to understand this distinction.",
      "keyPoints": ["Essential property 1", "Essential property 2", "Invariant 3"],
      "visual": {{"type": "definition", "title": "Term Anatomy", "data": {{}}}}
    }},
    {{
      "sceneNumber": 3,
      "slideType": "standard",
      "title": "Under the Hood: Deep Mechanism",
      "narration": "Step-by-step technical walkthrough of how the system/algorithm executes.",
      "keyPoints": ["Mechanism step 1", "Mechanism step 2", "Mechanism step 3"],
      "visual": {{
        "type": "flowchart",
        "title": "Execution Architecture",
        "data": {{"nodes": ["State A", "Check B", "Process C", "Output D"]}}
      }}
    }},
    {{
      "sceneNumber": 4,
      "slideType": "standard",
      "title": "Visual Architecture and Comparison",
      "narration": "Narration referencing the visual diagram or graph on screen, explaining each component.",
      "keyPoints": ["Structural insight 1", "Structural insight 2"],
      "visual": {{
        "type": "bar-chart|tree|comparison-table|flowchart",
        "title": "Data or Architecture Breakdown",
        "data": {{
          "labels": ["Case 1", "Case 2", "Case 3"],
          "values": [20, 50, 85]
        }}
      }}
    }},
    {{
      "sceneNumber": 5,
      "slideType": "quiz",
      "title": "Checkpoint: Knowledge Check",
      "narration": "Spoken quiz presentation. Read the question, give the student a pause to think, then reveal the correct answer and explain why it is correct.",
      "quiz": {{
        "question": "Challenging conceptual question testing understanding of the topic?",
        "options": ["Correct option text", "Plausible distractor 1", "Plausible distractor 2", "Plausible distractor 3"],
        "answerIndex": 0,
        "explanation": "Detailed technical explanation explaining why Option A is correct and why other choices fail."
      }}
    }},
    {{
      "sceneNumber": 6,
      "slideType": "standard",
      "title": "Summary, Common Pitfalls and Exam Tips",
      "narration": "Comprehensive wrap-up summarizing key rules, typical student errors, and memory hooks.",
      "keyPoints": ["Final rule 1", "Pitfall to avoid", "Exam takeaway"],
      "visual": {{
        "type": "flowchart",
        "title": "Mastery Roadmap",
        "data": {{"nodes": ["Core Concept", "Implementation", "Verification", "Mastery"]}}
      }}
    }}
  ]
}}

Rules:
- Language: {language}; Target audience: {level}; Teaching style: {style}; Target duration: ~{duration} minutes.
- Strictly ground all facts in the supplied study material.
- Narration must sound like a real, enthusiastic human professor explaining every detail.
- Provide 5 to 7 rich scenes. Ensure at least one dedicated definition slide and at least one quiz slide.
- No generic markdown wrappers around JSON.

SUPPLIED STUDY MATERIAL:
{clean[:14000]}
"""
    try:
        raw = _generate_with_ollama(prompt)
        parsed = _parse_json(raw)
        scenes = parsed.get("scenes", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
        if not scenes or len(scenes) < 3:
            raise ValueError("LLM returned insufficient scenes.")

        for i, sc in enumerate(scenes):
            sc.setdefault("sceneNumber", i + 1)
            sc.setdefault("title", f"Section {i + 1}")
            sc.setdefault("slideType", "standard")
            sc.setdefault("keyPoints", [])
            sc.setdefault("visual", {"type": "flowchart", "title": "Concept Flow", "data": {}})

        return scenes
    except Exception:
        if not _offline_fallback_enabled():
            raise
        return _offline_masterclass_curriculum(clean, options)


def generate_scene(page_text: str, page_number: int, options=None):
    options = options or {}
    curriculum = generate_curriculum(page_text, options)
    if curriculum:
        idx = min(page_number - 1, len(curriculum) - 1)
        return curriculum[idx if idx >= 0 else 0]
    return _offline_masterclass_curriculum(page_text, options)[0]


def generate_script(page_text: str, page_number: int, options=None) -> str:
    return generate_scene(page_text, page_number, options).get("narration", "")
