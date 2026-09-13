import unittest
import sys
import os
import json

# Set standard output encoding to utf-8 if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.pdf_extractor import PDFExtractor
from services.question_generator import QuestionGenerator
from services.test_manager import TestManager
from sample_pdf_creator import generate_sample_academic_pdf
from app import app

class TestAIStudyMate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf_path = generate_sample_academic_pdf("uploads/sample_machine_learning_primer.pdf")
        cls.app_client = app.test_client()

    def test_01_pdf_extractor(self):
        result = PDFExtractor.extract_from_file(self.pdf_path)
        self.assertIn("filename", result)
        self.assertGreaterEqual(result["total_pages"], 4)
        self.assertGreater(result["total_words"], 100)
        self.assertGreaterEqual(len(result["chunks"]), 1)
        print(f"[PASS] PDFExtractor: {result['total_words']} words, {result['total_pages']} pages extracted.")

    def test_02_question_generator(self):
        extraction_data = PDFExtractor.extract_from_file(self.pdf_path)
        bank = QuestionGenerator.generate_question_bank(extraction_data)
        self.assertIn("questions", bank)
        questions = bank["questions"]
        self.assertGreaterEqual(len(questions), 10)
        
        # Verify MCQ invariants
        for q in questions:
            self.assertEqual(len(q["options"]), 4, "MCQ must have exactly 4 options")
            self.assertIn(q["correct_answer"], [0, 1, 2, 3], "Correct answer index must be 0, 1, 2, or 3")
            self.assertTrue(len(q["question"]) > 5, "Question prompt must be non-empty")
            self.assertTrue(len(q["explanation"]) > 5, "Explanation must be non-empty")
            self.assertIn(q["difficulty"], ["Easy", "Medium", "Hard"])
        
        print(f"[PASS] QuestionGenerator: {len(questions)} verified MCQs generated.")

    def test_03_test_manager_session(self):
        test_session = TestManager.create_test_session(question_count=10, difficulty="Mixed")
        self.assertIn("session_id", test_session)
        self.assertEqual(len(test_session["questions"]), 10)
        self.assertEqual(test_session["time_limit_per_question"], 60)
        
        # Verify correct answer is NOT leaked in client questions
        for q in test_session["questions"]:
            self.assertNotIn("correct_answer", q, "Client payload must NOT expose correct answer during test")
        
        # Simulate answers: 8 correct, 1 wrong, 1 unanswered
        session_id = test_session["session_id"]
        server_session = TestManager._active_sessions[session_id]
        ground_truth = server_session["ground_truth"]
        
        answers = {}
        for idx in range(1, 9): # 8 correct
            answers[str(idx)] = ground_truth[str(idx)]["correct_answer"]
        # 1 wrong
        wrong_idx = (ground_truth["9"]["correct_answer"] + 1) % 4
        answers["9"] = wrong_idx
        # question 10 left unanswered
        answers["10"] = None

        evaluation = TestManager.evaluate_test_session(session_id, answers)
        self.assertEqual(evaluation["total_questions"], 10)
        self.assertEqual(evaluation["correct_count"], 8)
        self.assertEqual(evaluation["wrong_count"], 1)
        self.assertEqual(evaluation["unanswered_count"], 1)
        self.assertEqual(evaluation["score_percentage"], 80)
        self.assertEqual(evaluation["tier_title"], "Very Good")
        self.assertGreaterEqual(len(evaluation["topic_breakdown"]), 1)
        self.assertEqual(len(evaluation["review_cards"]), 10)
        print(f"[PASS] TestManager: Evaluation validated. Score = {evaluation['score_percentage']}%.")

    def test_04_flask_routes(self):
        # Landing page
        res = self.app_client.get("/")
        self.assertEqual(res.status_code, 200)

        # Upload page
        res = self.app_client.get("/upload")
        self.assertEqual(res.status_code, 200)

        # Setup test page
        res = self.app_client.get("/setup-test")
        self.assertEqual(res.status_code, 200)

        # API Start Test
        res = self.app_client.post("/api/start-test", json={"question_count": 10, "difficulty": "Mixed"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        print("[PASS] Flask routes & API endpoints responded with HTTP 200.")

if __name__ == "__main__":
    unittest.main()
