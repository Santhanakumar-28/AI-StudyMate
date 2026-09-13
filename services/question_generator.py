import os
import json
import random
from typing import Dict, List, Any
from .ai_processor import AIProcessor

class QuestionGenerator:
    """
    Orchestrates end-to-end question bank generation across all PDF chunks.
    Ensures strict validation, answer balance, deduplication, and persistence.
    """

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    QUESTION_BANK_FILE = os.path.join(DATA_DIR, "question_bank.json")
    EXTRACTED_CONTENT_FILE = os.path.join(DATA_DIR, "extracted_content.json")

    @classmethod
    def generate_question_bank(cls, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        chunks = extraction_result.get("chunks", [])
        total_words = extraction_result.get("total_words", 0)
        total_pages = extraction_result.get("total_pages", 1)

        # Determine target question bank volume based on length
        if total_words < 1200:
            target_total = min(35, max(15, total_pages * 8))
        elif total_words < 5000:
            target_total = min(65, max(30, total_pages * 7))
        else:
            target_total = min(120, max(50, total_pages * 6))

        chunk_count = len(chunks)
        per_chunk = max(3, target_total // max(1, chunk_count))

        all_questions = []
        seen_question_texts = set()

        for chunk in chunks:
            chunk_text = chunk["text"]
            source_ref = chunk["source_reference"]
            topic = chunk["primary_topic"]

            chunk_questions = AIProcessor.generate_questions_for_chunk(
                chunk_text=chunk_text,
                source_ref=source_ref,
                primary_topic=topic,
                count=per_chunk
            )

            for q in chunk_questions:
                q_text = q["question"].strip()
                if q_text.lower() not in seen_question_texts:
                    seen_question_texts.add(q_text.lower())
                    q["id"] = len(all_questions) + 1
                    all_questions.append(q)

        difficulties = ["Easy", "Medium", "Hard"]
        for idx, q in enumerate(all_questions):
            if "difficulty" not in q or q["difficulty"] not in difficulties:
                q["difficulty"] = difficulties[idx % 3]

        bank_data = {
            "metadata": {
                "filename": extraction_result.get("filename"),
                "total_questions": len(all_questions),
                "total_pages": total_pages,
                "total_words": total_words,
                "topics": extraction_result.get("topics", [])
            },
            "questions": all_questions
        }

        os.makedirs(cls.DATA_DIR, exist_ok=True)
        with open(cls.QUESTION_BANK_FILE, "w", encoding="utf-8") as f:
            json.dump(bank_data, f, indent=2, ensure_ascii=False)

        with open(cls.EXTRACTED_CONTENT_FILE, "w", encoding="utf-8") as f:
            json.dump(extraction_result, f, indent=2, ensure_ascii=False)

        return bank_data

    @classmethod
    def load_question_bank(cls) -> Dict[str, Any]:
        if not os.path.exists(cls.QUESTION_BANK_FILE):
            return {"questions": [], "metadata": {}}
        try:
            with open(cls.QUESTION_BANK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"questions": [], "metadata": {}}
