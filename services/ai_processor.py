import os
import json
import re
import random
from typing import Dict, List, Any, Optional
import requests

class AIProcessor:
    """
    Modular AI service provider supporting:
    - Google Gemini API (gemini-1.5-flash / gemini-2.0-flash / gemini-pro)
    - NVIDIA NIM API (meta/llama-3.1-70b-instruct, etc.)
    - OpenAI-compatible LLM endpoints
    - Intelligent Fallback Academic Engine (Grounded rule-based NLP question extractor)
    """

    @classmethod
    def get_provider_info(cls) -> Dict[str, Any]:
        provider = os.getenv("AI_PROVIDER", "gemini").lower()
        gemini_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("AI_API_KEY", "")
        nvidia_key = os.getenv("NVIDIA_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")

        has_key = bool(gemini_key or nvidia_key or openai_key)
        active_provider = provider if has_key else "academic_heuristic_engine"

        return {
            "configured_provider": provider,
            "active_provider": active_provider,
            "has_api_key": has_key,
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "nvidia_model": os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
        }

    @classmethod
    def generate_questions_for_chunk(
        cls,
        chunk_text: str,
        source_ref: str,
        primary_topic: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generates academic MCQs strictly grounded in the provided chunk text.
        """
        provider = os.getenv("AI_PROVIDER", "gemini").lower()
        gemini_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("AI_API_KEY", "")
        nvidia_key = os.getenv("NVIDIA_API_KEY", "")

        # Try API provider first if key is present
        if provider == "gemini" and gemini_key:
            try:
                questions = cls._call_gemini(chunk_text, source_ref, primary_topic, count, gemini_key)
                if questions and len(questions) > 0:
                    return questions
            except Exception as e:
                print(f"[AIProcessor] Gemini API call error: {e}. Falling back to Academic Engine.")

        elif (provider == "nvidia" or provider == "openai_compatible") and (nvidia_key or gemini_key):
            try:
                questions = cls._call_nvidia(chunk_text, source_ref, primary_topic, count)
                if questions and len(questions) > 0:
                    return questions
            except Exception as e:
                print(f"[AIProcessor] LLM API call error: {e}. Falling back to Academic Engine.")

        # High Quality Academic Fallback Engine (Strictly grounded in chunk text)
        return cls._generate_fallback_questions(chunk_text, source_ref, primary_topic, count)

    @classmethod
    def _get_system_prompt(cls, count: int, primary_topic: str, source_ref: str) -> str:
        return f"""You are an academic examination and interview preparation question generator.
Analyze ONLY the provided subject material.
Identify the most important concepts, definitions, classifications, comparisons, algorithms, processes, formulas, and key facts.
Generate EXACTLY {count} high-quality Multiple Choice Questions (MCQs) based STRICTLY on the provided text.

CRITICAL RULES:
1. Do NOT invent or assume information. Ground every single question and explanation strictly in the provided text.
2. Each question must have EXACTLY 4 distinct, plausible options.
3. Provide ONLY ONE correct answer index (0, 1, 2, or 3).
4. Balance the correct answer positions across 0, 1, 2, and 3 (do NOT make option 0 always correct).
5. Provide a concise 2-4 sentence explanation clearly stating why the correct answer is right according to the material.
6. Assign a realistic difficulty: "Easy", "Medium", or "Hard".
7. Assign the relevant topic (use "{primary_topic}" or a specific subtopic).
8. Use source reference: "{source_ref}".

You MUST return ONLY a valid JSON array of objects with this exact structure:
[
  {{
    "question": "Clear and specific question text?",
    "options": [
      "Option A text",
      "Option B text",
      "Option C text",
      "Option D text"
    ],
    "correct_answer": 0,
    "explanation": "2-4 sentences explaining the reasoning grounded in the source text.",
    "topic": "{primary_topic}",
    "difficulty": "Medium",
    "source_reference": "{source_ref}"
  }}
]
"""

    @classmethod
    def _call_gemini(
        cls,
        chunk_text: str,
        source_ref: str,
        primary_topic: str,
        count: int,
        api_key: str
    ) -> List[Dict[str, Any]]:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2}
        )

        prompt = f"{cls._get_system_prompt(count, primary_topic, source_ref)}\n\nSUBJECT MATERIAL:\n\"\"\"\n{chunk_text}\n\"\"\""
        response = model.generate_content(prompt)
        text_content = response.text or ""
        return cls._parse_and_validate_mcqs(text_content, source_ref, primary_topic)

    @classmethod
    def _call_nvidia(
        cls,
        chunk_text: str,
        source_ref: str,
        primary_topic: str,
        count: int
    ) -> List[Dict[str, Any]]:
        api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        system_msg = cls._get_system_prompt(count, primary_topic, source_ref)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Extract {count} exam MCQs from this material:\n\n{chunk_text}"}
            ],
            "temperature": 0.2,
            "max_tokens": 2048
        }

        resp = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return cls._parse_and_validate_mcqs(content, source_ref, primary_topic)

    @classmethod
    def _parse_and_validate_mcqs(cls, raw_text: str, source_ref: str, fallback_topic: str) -> List[Dict[str, Any]]:
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
            raw_text = re.sub(r"\n```$", "", raw_text)

        try:
            items = json.loads(raw_text)
        except Exception:
            match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
            if match:
                try:
                    items = json.loads(match.group(0))
                except Exception:
                    return []
            else:
                return []

        if not isinstance(items, list):
            if isinstance(items, dict) and "questions" in items:
                items = items["questions"]
            else:
                return []

        validated = []
        for item in items:
            if not isinstance(item, dict):
                continue
            question = item.get("question", "").strip()
            options = item.get("options", [])
            correct = item.get("correct_answer", 0)
            explanation = item.get("explanation", "").strip()
            topic = item.get("topic", fallback_topic).strip() or fallback_topic
            difficulty = item.get("difficulty", "Medium")

            if not question or not isinstance(options, list) or len(options) != 4:
                continue

            cleaned_options = [str(opt).strip() for opt in options]
            if len(set(cleaned_options)) != 4:
                continue

            try:
                correct_idx = int(correct)
                if correct_idx < 0 or correct_idx > 3:
                    correct_idx = 0
            except Exception:
                correct_idx = 0

            if not explanation:
                explanation = f"Based on {source_ref}, the correct concept is {cleaned_options[correct_idx]}."

            if difficulty not in ["Easy", "Medium", "Hard"]:
                difficulty = "Medium"

            validated.append({
                "question": question,
                "options": cleaned_options,
                "correct_answer": correct_idx,
                "explanation": explanation,
                "topic": topic,
                "difficulty": difficulty,
                "source_reference": item.get("source_reference", source_ref)
            })

        return validated

    @classmethod
    def _generate_fallback_questions(
        cls,
        chunk_text: str,
        source_ref: str,
        primary_topic: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Grounded academic NLP concept extractor that parses definitions, key rules,
        processes, and facts directly from the chunk text.
        """
        sentences = re.split(r'(?<=[.!?])\s+', chunk_text)
        cleaned_sentences = [s.strip() for s in sentences if len(s.strip()) > 25 and not s.startswith("--- Page")]

        questions = []
        seen_questions = set()

        def_patterns = [
            r'([A-Z][A-Za-z0-9\s\-]{2,35})\s+(?:is defined as|refers to|is a type of|is an algorithm that|is used for|means)\s+([^.,;]{15,160})',
            r'([A-Z][A-Za-z0-9\s\-]{2,35})\s+(?:consists of|enables|provides|calculates|operates by)\s+([^.,;]{15,160})',
            r'(?:The purpose of|The primary goal of)\s+([A-Z][A-Za-z0-9\s\-]{2,35})\s+is\s+([^.,;]{15,160})'
        ]

        extracted_concepts = []
        for s in cleaned_sentences:
            for pat in def_patterns:
                matches = re.findall(pat, s, re.IGNORECASE)
                for term, definition in matches:
                    term_clean = term.strip()
                    def_clean = definition.strip()
                    if len(term_clean) > 2 and len(def_clean) > 10 and term_clean.lower() not in ["it", "this", "these", "there", "which", "they"]:
                        extracted_concepts.append((term_clean, def_clean, s))

        distractor_verbs = [
            "Minimizes computational latency through inline caching.",
            "Executes arbitrary code in unverified memory segments.",
            "Bypasses standard evaluation criteria during runtime.",
            "Processes unlabelled data without external supervision.",
            "Aggregates external network requests sequentially.",
            "Reverses gradient propagation unconditionally.",
            "Stores intermediate calculations permanently on disk.",
            "Applies statistical normalization across all attributes."
        ]

        for term, definition, full_sent in extracted_concepts:
            if len(questions) >= count:
                break

            q_text = f"According to the material, what best describes '{term}'?"
            if q_text in seen_questions:
                continue

            correct_opt = definition[0].upper() + definition[1:]
            if not correct_opt.endswith('.'):
                correct_opt += '.'

            distractors = []
            other_defs = [c[1][0].upper() + c[1][1:] + '.' for c in extracted_concepts if c[0].lower() != term.lower()]
            random.shuffle(other_defs)
            for d in other_defs:
                if d != correct_opt and d not in distractors:
                    distractors.append(d)
                if len(distractors) == 3:
                    break

            while len(distractors) < 3:
                d_cand = random.choice(distractor_verbs)
                if d_cand != correct_opt and d_cand not in distractors:
                    distractors.append(d_cand)

            options = [correct_opt] + distractors[:3]
            correct_idx = random.randint(0, 3)
            options[0], options[correct_idx] = options[correct_idx], options[0]

            seen_questions.add(q_text)
            questions.append({
                "question": q_text,
                "options": options,
                "correct_answer": correct_idx,
                "explanation": f"As stated in the material: \"{full_sent.strip()}\"",
                "topic": primary_topic,
                "difficulty": random.choice(["Easy", "Medium", "Hard"]),
                "source_reference": source_ref
            })

        if len(questions) < count:
            for s in cleaned_sentences:
                if len(questions) >= count:
                    break
                words = s.split()
                if 8 <= len(words) <= 38:
                    q_text = f"Which of the following statements is TRUE regarding {primary_topic}?"
                    if q_text in seen_questions:
                        continue

                    correct_opt = s if s.endswith('.') else s + '.'
                    distractors = [
                        f"{primary_topic} does not apply under the conditions described in the text.",
                        f"{primary_topic} strictly prohibits iterative optimization and validation.",
                        f"{primary_topic} is exclusively executed in offline hardware environments."
                    ]
                    options = [correct_opt] + distractors
                    correct_idx = random.randint(0, 3)
                    options[0], options[correct_idx] = options[correct_idx], options[0]

                    seen_questions.add(q_text)
                    questions.append({
                        "question": q_text,
                        "options": options,
                        "correct_answer": correct_idx,
                        "explanation": f"According to the document: \"{s.strip()}\"",
                        "topic": primary_topic,
                        "difficulty": "Medium",
                        "source_reference": source_ref
                    })

        return questions[:count]
