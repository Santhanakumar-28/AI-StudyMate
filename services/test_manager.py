import os
import json
import uuid
import random
import time
from typing import Dict, List, Any, Optional
from .question_generator import QuestionGenerator

class TestManager:
    """
    Manages mock test setup, question randomization, option shuffling,
    60s timer parameters, grading, and in-depth performance analysis.
    """

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    TEST_RESULTS_FILE = os.path.join(DATA_DIR, "test_results.json")

    # In-memory active session store (for server-side ground truth verification)
    _active_sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_test_session(
        cls,
        question_count: int = 20,
        difficulty: str = "Mixed",
        topics_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        bank_data = QuestionGenerator.load_question_bank()
        questions = bank_data.get("questions", [])

        if not questions:
            raise ValueError("No questions available in the question bank. Please upload a PDF first.")

        # Filter by difficulty
        if difficulty and difficulty != "Mixed":
            filtered = [q for q in questions if q.get("difficulty") == difficulty]
            if len(filtered) >= 5:
                pool = filtered
            else:
                pool = questions
        else:
            pool = questions

        # Filter by topics if provided
        if topics_filter and len(topics_filter) > 0:
            topic_filtered = [q for q in pool if q.get("topic") in topics_filter]
            if len(topic_filtered) >= 5:
                pool = topic_filtered

        # Select random sample
        sample_size = min(question_count, len(pool))
        selected_questions = random.sample(pool, sample_size)

        session_id = str(uuid.uuid4())
        session_questions_client = []
        ground_truth = {}

        for idx, q in enumerate(selected_questions):
            q_num = idx + 1
            # Randomize option order for this test instance
            original_options = list(q["options"])
            orig_correct_idx = q["correct_answer"]
            correct_opt_text = original_options[orig_correct_idx]

            shuffled_options = list(original_options)
            random.shuffle(shuffled_options)
            new_correct_idx = shuffled_options.index(correct_opt_text)

            # Ground truth kept safe on server
            ground_truth[str(q_num)] = {
                "question": q["question"],
                "options": shuffled_options,
                "correct_answer": new_correct_idx,
                "correct_text": correct_opt_text,
                "explanation": q.get("explanation", ""),
                "topic": q.get("topic", "General Concepts"),
                "difficulty": q.get("difficulty", "Medium"),
                "source_reference": q.get("source_reference", "")
            }

            # Client receives questions WITHOUT correct answers
            session_questions_client.append({
                "number": q_num,
                "question": q["question"],
                "options": shuffled_options,
                "topic": q.get("topic", "General Concepts"),
                "difficulty": q.get("difficulty", "Medium"),
                "time_limit_seconds": 60
            })

        cls._active_sessions[session_id] = {
            "session_id": session_id,
            "created_at": time.time(),
            "ground_truth": ground_truth,
            "total_questions": len(session_questions_client),
            "difficulty_setting": difficulty,
            "filename": bank_data.get("metadata", {}).get("filename", "Subject PDF")
        }

        return {
            "session_id": session_id,
            "total_questions": len(session_questions_client),
            "time_limit_per_question": 60,
            "questions": session_questions_client,
            "source_filename": bank_data.get("metadata", {}).get("filename", "Subject PDF")
        }

    @classmethod
    def evaluate_test_session(
        cls,
        session_id: str,
        user_answers: Dict[str, Any],
        client_test_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates test responses against ground truth.
        Computes score %, breakdown, performance tier, topic mastery, and review cards.
        """
        session = cls._active_sessions.get(session_id)
        if not session and client_test_data and "ground_truth" in client_test_data:
            ground_truth = client_test_data["ground_truth"]
            source_filename = client_test_data.get("filename", "Subject PDF")
        elif session:
            ground_truth = session["ground_truth"]
            source_filename = session.get("filename", "Subject PDF")
        else:
            bank_data = QuestionGenerator.load_question_bank()
            questions = bank_data.get("questions", [])
            source_filename = bank_data.get("metadata", {}).get("filename", "Subject PDF")
            ground_truth = {}
            for idx, q in enumerate(questions[:max(1, len(user_answers))]):
                ground_truth[str(idx + 1)] = q

        total_questions = len(ground_truth)
        if total_questions == 0:
            raise ValueError("Invalid test session or empty question set.")

        correct_count = 0
        wrong_count = 0
        unanswered_count = 0

        topic_stats: Dict[str, Dict[str, int]] = {}
        review_cards: List[Dict[str, Any]] = []

        for q_num_str, q_info in ground_truth.items():
            q_num = int(q_num_str)
            correct_idx = q_info["correct_answer"]
            options = q_info["options"]
            topic = q_info.get("topic", "General Concepts")

            if topic not in topic_stats:
                topic_stats[topic] = {"total": 0, "correct": 0}
            topic_stats[topic]["total"] += 1

            user_choice = user_answers.get(q_num_str)
            if user_choice is None or user_choice == "" or user_choice == -1 or user_choice == "null":
                user_selected_idx = None
                user_selected_text = "Not Answered"
                status = "unanswered"
                unanswered_count += 1
            else:
                try:
                    user_selected_idx = int(user_choice)
                    if 0 <= user_selected_idx < len(options):
                        user_selected_text = options[user_selected_idx]
                        if user_selected_idx == correct_idx:
                            status = "correct"
                            correct_count += 1
                            topic_stats[topic]["correct"] += 1
                        else:
                            status = "wrong"
                            wrong_count += 1
                    else:
                        user_selected_idx = None
                        user_selected_text = "Not Answered"
                        status = "unanswered"
                        unanswered_count += 1
                except Exception:
                    user_selected_idx = None
                    user_selected_text = "Not Answered"
                    status = "unanswered"
                    unanswered_count += 1

            review_cards.append({
                "question_number": q_num,
                "question": q_info["question"],
                "options": options,
                "user_selected_index": user_selected_idx,
                "user_selected_text": user_selected_text,
                "correct_index": correct_idx,
                "correct_text": options[correct_idx],
                "status": status,
                "is_correct": (status == "correct"),
                "explanation": q_info.get("explanation", "Refer to the source material."),
                "topic": topic,
                "difficulty": q_info.get("difficulty", "Medium"),
                "source_reference": q_info.get("source_reference", "")
            })

        review_cards.sort(key=lambda x: x["question_number"])

        score_percentage = round((correct_count / total_questions) * 100)

        # Performance Tier based on specifications
        if score_percentage >= 90:
            tier_title = "Excellent"
            tier_message = "Excellent performance! You have a strong understanding of the material."
            badge_color = "emerald"
        elif score_percentage >= 75:
            tier_title = "Very Good"
            tier_message = "Very good understanding! You have grasped the core subject concepts well."
            badge_color = "indigo"
        elif score_percentage >= 60:
            tier_title = "Good"
            tier_message = "Good foundation, but a few key topics require targeted revision."
            badge_color = "blue"
        elif score_percentage >= 40:
            tier_title = "Needs Improvement"
            tier_message = "Needs improvement. Review the explanations and revisit weak topics."
            badge_color = "amber"
        else:
            tier_title = "Keep Practicing"
            tier_message = "Keep practicing. Thoroughly study your mistakes and review the PDF material."
            badge_color = "rose"

        # Topic breakdown
        topic_breakdown = []
        for t_name, t_data in topic_stats.items():
            t_pct = round((t_data["correct"] / t_data["total"]) * 100) if t_data["total"] > 0 else 0
            topic_breakdown.append({
                "topic": t_name,
                "total": t_data["total"],
                "correct": t_data["correct"],
                "percentage": t_pct
            })
        topic_breakdown.sort(key=lambda x: x["percentage"], reverse=True)

        result_payload = {
            "test_id": session_id,
            "filename": source_filename,
            "timestamp": time.time(),
            "total_questions": total_questions,
            "score_percentage": score_percentage,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "unanswered_count": unanswered_count,
            "tier_title": tier_title,
            "tier_message": tier_message,
            "badge_color": badge_color,
            "topic_breakdown": topic_breakdown,
            "review_cards": review_cards
        }

        cls._save_result(result_payload)
        return result_payload

    @classmethod
    def _save_result(cls, result_data: Dict[str, Any]):
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        results = []
        if os.path.exists(cls.TEST_RESULTS_FILE):
            try:
                with open(cls.TEST_RESULTS_FILE, "r", encoding="utf-8") as f:
                    results = json.load(f)
            except Exception:
                results = []

        results.insert(0, result_data)
        results = results[:25]

        try:
            with open(cls.TEST_RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving test result: {e}")

    @classmethod
    def get_result_by_id(cls, test_id: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(cls.TEST_RESULTS_FILE):
            return None
        try:
            with open(cls.TEST_RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
                for r in results:
                    if r.get("test_id") == test_id:
                        return r
        except Exception:
            return None
        return None
