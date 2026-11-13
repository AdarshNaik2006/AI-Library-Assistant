import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import io
import urllib.error
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from database.db import (
    seed_database,
    search_resources,
    get_all_subjects,
    get_all_education_levels,
    get_all_departments,
    add_resource,
    get_resource_by_id,
    get_connection,
)
import assistant


class TestDatabase(unittest.TestCase):
    def setUp(self):
        seed_database()

    def test_seed_database_idempotent(self):
        """Verify seeding preserves data and does not insert duplicates when called repeatedly."""
        with get_connection() as conn:
            initial_count = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]

        self.assertGreater(initial_count, 0)

        # Seed again
        seed_database()

        with get_connection() as conn:
            second_count = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]

        self.assertEqual(initial_count, second_count, "Database seeding must not create duplicate records")

    def test_search_resources_filters(self):
        """Verify query search, subject filtering, level filtering, and education level filtering."""
        # Query search
        python_items = search_resources(query="Python")
        self.assertTrue(any("Python" in r["title"] for r in python_items))

        # Subject filter
        os_items = search_resources(subject="Operating Systems")
        self.assertTrue(len(os_items) > 0)
        for r in os_items:
            self.assertEqual(r["subject"], "Operating Systems")

        # Education level filter
        primary_items = search_resources(education_level="Primary School")
        self.assertTrue(len(primary_items) > 0)
        for r in primary_items:
            self.assertEqual(r["education_level"], "Primary School")

        # Class grade filter
        class3_items = search_resources(class_grade="Class 3")
        self.assertTrue(len(class3_items) > 0)
        for r in class3_items:
            self.assertEqual(r["class_grade"], "Class 3")

        # Nonexistent query
        none_items = search_resources(query="NonExistentBookXYZ12345")
        self.assertEqual(len(none_items), 0)

    def test_get_all_subjects(self):
        """Verify get_all_subjects returns subjects across school and college."""
        subjects = get_all_subjects()
        self.assertIn("Mathematics", subjects)
        self.assertIn("Science", subjects)
        self.assertIn("Physics", subjects)
        self.assertIn("Engineering Mathematics", subjects)
        self.assertIn("Python Programming", subjects)
        self.assertIn("Operating Systems", subjects)

    def test_get_all_education_levels(self):
        """Verify distinct education levels are retrieved from database."""
        levels = get_all_education_levels()
        self.assertIn("Primary School", levels)
        self.assertIn("Middle School", levels)
        self.assertIn("High School", levels)
        self.assertIn("PUC", levels)
        self.assertIn("Diploma", levels)
        self.assertIn("Undergraduate", levels)
        self.assertIn("Postgraduate", levels)

    def test_add_and_retrieve_resource(self):
        """Verify manual resource addition with full metadata and retrieval by ID."""
        new_id = add_resource(
            title="Test CS Book",
            author="Test Author",
            subject="Computer Networks",
            level="Beginner",
            description="A test description.",
            resource_type="Book",
            url="https://example.com/test",
            education_level="Undergraduate",
            class_grade="All Classes",
            department="Computer Science",
            language="English",
        )
        self.assertIsNotNone(new_id)

        retrieved = get_resource_by_id(new_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["title"], "Test CS Book")
        self.assertEqual(retrieved["education_level"], "Undergraduate")


class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_frontend_serving(self):
        """Verify the frontend index.html and static assets are served properly."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Verify chat input form layout order: below header and suggestions, above chat messages
        suggestions_pos = html.find('class="suggestions-wrapper"')
        form_pos = html.find('id="chatForm"')
        messages_pos = html.find('id="chatMessages"')
        self.assertGreater(suggestions_pos, 0)
        self.assertGreater(form_pos, suggestions_pos, "Chat form must be positioned below suggestions")
        self.assertGreater(messages_pos, form_pos, "Chat messages must be positioned below the chat input form")

        # Static css
        css_res = self.client.get("/css/style.css")
        self.assertEqual(css_res.status_code, 200)
        self.assertIn(b"--primary-color", css_res.data)

        # Static js
        js_res = self.client.get("/js/script.js")
        self.assertEqual(js_res.status_code, 200)
        self.assertIn(b"conversationHistory", js_res.data)

    @patch("app.check_ollama_status")
    def test_health_endpoint(self, mock_status):
        """Verify GET /api/health returns database connectivity and Ollama status."""
        mock_status.return_value = {
            "connected": True,
            "model_available": True,
            "model": "llama3.2:3b",
            "installed_models": ["llama3.2:3b"],
            "url": "http://localhost:11434",
        }
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertEqual(data["ai_provider"], "Ollama (Local)")
        self.assertTrue(data["ai_connected"])
        self.assertTrue(data["model_available"])

    def test_subjects_endpoint(self):
        """Verify GET /api/subjects returns subject list."""
        response = self.client.get("/api/subjects")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("subjects", data)
        self.assertIsInstance(data["subjects"], list)
        self.assertGreater(len(data["subjects"]), 0)

    def test_education_levels_endpoint(self):
        """Verify GET /api/education-levels returns list of educational tiers."""
        response = self.client.get("/api/education-levels")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("education_levels", data)
        self.assertIn("Primary School", data["education_levels"])
        self.assertIn("PUC", data["education_levels"])

    def test_resources_endpoint(self):
        """Verify GET /api/resources returns catalogue resources and handles multi-tier filters."""
        # Unfiltered
        res = self.client.get("/api/resources")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["count"], 0)

        # Filtered by education_level
        res_edu = self.client.get("/api/resources?education_level=PUC")
        self.assertEqual(res_edu.status_code, 200)
        data_edu = res_edu.get_json()
        self.assertTrue(data_edu["success"])
        for r in data_edu["resources"]:
            self.assertEqual(r["education_level"], "PUC")

        # Filtered by class_grade
        res_cls = self.client.get("/api/resources?class_grade=Class 5")
        self.assertEqual(res_cls.status_code, 200)
        data_cls = res_cls.get_json()
        self.assertTrue(data_cls["success"])
        for r in data_cls["resources"]:
            self.assertEqual(r["class_grade"], "Class 5")

    def test_chat_validation(self):
        """Verify /api/chat validates request format and required fields."""
        # Missing JSON body
        res = self.client.post("/api/chat", data="not json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

        # Empty message
        res = self.client.post("/api/chat", json={"message": "   "})
        self.assertEqual(res.status_code, 400)

        # Missing message key
        res = self.client.post("/api/chat", json={"history": []})
        self.assertEqual(res.status_code, 400)

    def test_chat_ollama_not_running_graceful_handling(self):
        """Verify /api/chat returns a helpful response without crashing when Ollama is offline."""
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            res = self.client.post("/api/chat", json={"message": "Suggest Python books for beginners."})
            self.assertEqual(res.status_code, 503)
            data = res.get_json()
            self.assertFalse(data["success"])
            self.assertEqual(data["error_type"], "ollama_not_running")
            self.assertIn("ollama serve", data["message"].lower())


class TestUniversalLibraryScenarios(unittest.TestCase):
    """
    Automated tests verifying the 11 specific scenarios requested by the user:
    1. 3rd Standard English book recommendations.
    2. 5th Standard Kannada mathematics recommendations.
    3. 8th Standard Science explanations.
    4. 10th Standard Mathematics recommendations.
    5. 2nd PUC Physics recommendations.
    6. Diploma-level subject recommendations.
    7. Engineering Mathematics M2 recommendations.
    8. Python book recommendations.
    9. Kannada questions and Kannada responses.
    10. English questions and English responses.
    11. Unrelated questions (biryani, cricket, jokes) rejected in both English and Kannada.
    """

    def setUp(self):
        self.client = app.test_client()

    # -------------------------------------------------------------------------
    # Scenario 1: 3rd Standard English book recommendations
    # -------------------------------------------------------------------------
    def test_scenario_1_third_standard_english_recommendations(self):
        """Verify 3rd Standard English query recommends verified Class 3 English books and no unrelated books."""
        query = "3rd Standard English book recommendations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0, "Must find Class 3 English books in catalogue")

        # Verify exact match
        titles = [r["title"] for r in resources]
        self.assertTrue(any("Marigold" in t for t in titles), "Must recommend Marigold Class 3 English")

        # Verify strict negative constraint: No computer science or unrelated high school books
        for r in resources:
            self.assertEqual(r["education_level"], "Primary School")
            self.assertEqual(r["class_grade"], "Class 3")
            self.assertEqual(r["subject"], "English")

    # -------------------------------------------------------------------------
    # Scenario 2: 5th Standard Kannada mathematics recommendations
    # -------------------------------------------------------------------------
    def test_scenario_2_fifth_standard_kannada_mathematics_recommendations(self):
        """Verify 5th Standard Kannada mathematics query returns genuine Class 5 Mathematics books."""
        # English query with Kannada subject/medium
        query_en = "5th Standard Kannada mathematics recommendations."
        self.assertTrue(assistant.is_in_domain(query_en))
        resources_en = assistant.find_relevant_resources(query_en)
        self.assertGreater(len(resources_en), 0)
        titles_en = [r["title"] for r in resources_en]
        self.assertTrue(
            any("Ganitha Prakash" in t or "Math-Magic" in t or "ಗಣಿತ ಪ್ರಕಾಶ" in t for t in titles_en),
            "Must recommend Class 5 Mathematics textbook"
        )
        for r in resources_en:
            self.assertEqual(r["class_grade"], "Class 5")
            self.assertIn(r["subject"], ["Mathematics", "Kannada"])

        # Native Kannada query
        query_kn = "5ನೇ ತರಗತಿಯ ಗಣಿತ ಪುಸ್ತಕ ಶಿಫಾರಸು ಮಾಡಿ"
        self.assertTrue(assistant.is_in_domain(query_kn))
        resources_kn = assistant.find_relevant_resources(query_kn)
        self.assertGreater(len(resources_kn), 0)
        titles_kn = [r["title"] for r in resources_kn]
        self.assertTrue(
            any("Ganitha Prakash" in t or "Math-Magic" in t or "ಗಣಿತ ಪ್ರಕಾಶ" in t for t in titles_kn),
            "Must recommend Class 5 Mathematics textbook for Kannada query"
        )

    # -------------------------------------------------------------------------
    # Scenario 3: 8th Standard Science explanations
    # -------------------------------------------------------------------------
    def test_scenario_3_eighth_standard_science_explanations(self):
        """Verify 8th Standard Science query is in-domain and matches Class 8 Science textbook."""
        query = "8th Standard Science explanations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0)
        titles = [r["title"] for r in resources]
        self.assertTrue(any("Class VIII" in t or "೮ನೇ ತರಗತಿ" in t for t in titles))
        for r in resources:
            self.assertEqual(r["class_grade"], "Class 8")
            self.assertEqual(r["subject"], "Science")

    # -------------------------------------------------------------------------
    # Scenario 4: 10th Standard Mathematics recommendations
    # -------------------------------------------------------------------------
    def test_scenario_4_tenth_standard_mathematics_recommendations(self):
        """Verify 10th Standard Mathematics query recommends authentic SSLC / Class X textbooks."""
        query = "10th Standard Mathematics recommendations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0)
        titles = [r["title"] for r in resources]
        self.assertTrue(
            any("Class X" in t or "೧೦ನೇ ತರಗತಿ" in t or "R.S. Aggarwal" in t for t in titles),
            "Must recommend authentic Class 10 / SSLC Mathematics textbooks"
        )
        for r in resources:
            self.assertEqual(r["class_grade"], "Class 10")
            self.assertEqual(r["subject"], "Mathematics")

    # -------------------------------------------------------------------------
    # Scenario 5: 2nd PUC Physics recommendations
    # -------------------------------------------------------------------------
    def test_scenario_5_second_puc_physics_recommendations(self):
        """Verify 2nd PUC Physics query recommends genuine NCERT / Karnataka PUE textbooks."""
        query = "2nd PUC Physics recommendations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0)
        titles = [r["title"] for r in resources]
        self.assertTrue(any("2nd PUC Physics" in t or "Class XII" in t for t in titles))
        for r in resources:
            self.assertEqual(r["education_level"], "PUC")
            self.assertEqual(r["class_grade"], "2nd PUC")
            self.assertEqual(r["subject"], "Physics")

    # -------------------------------------------------------------------------
    # Scenario 6: Diploma-level subject recommendations
    # -------------------------------------------------------------------------
    def test_scenario_6_diploma_level_subject_recommendations(self):
        """Verify Diploma-level query recommends genuine polytechnic curriculum textbooks."""
        query = "Diploma-level subject recommendations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0)
        for r in resources:
            self.assertEqual(r["education_level"], "Diploma")
        titles = [r["title"] for r in resources]
        self.assertTrue(any("Applied Science" in t or "Diploma" in t or "Polytechnic" in t for t in titles))

    # -------------------------------------------------------------------------
    # Scenario 7: Engineering Mathematics M2 recommendations
    # -------------------------------------------------------------------------
    def test_scenario_7_engineering_mathematics_m2_recommendations(self):
        """Verify M2 recommendations return standard higher engineering math books and NO school books."""
        query = "Engineering Mathematics M2 recommendations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0)
        authors = [r["author"] for r in resources]
        # Must match Dr. B.S. Grewal, Erwin Kreyszig, or Bali & Goyal
        self.assertTrue(
            any("Grewal" in a or "Kreyszig" in a or "Bali" in a for a in authors),
            "Must recommend university-standard M2 textbooks"
        )
        # Must NOT return school-level books
        for r in resources:
            self.assertNotEqual(r["education_level"], "Primary School")
            self.assertNotEqual(r["education_level"], "Middle School")

    # -------------------------------------------------------------------------
    # Scenario 8: Python book recommendations
    # -------------------------------------------------------------------------
    def test_scenario_8_python_book_recommendations(self):
        """Verify Python query recommends established Python textbooks from the catalogue."""
        query = "Python book recommendations."
        self.assertTrue(assistant.is_in_domain(query))

        resources = assistant.find_relevant_resources(query)
        self.assertGreater(len(resources), 0)
        titles = [r["title"] for r in resources]
        self.assertTrue(
            any("Python Crash Course" in t or "Automate the Boring Stuff" in t or "Fluent Python" in t for t in titles)
        )
        for r in resources:
            self.assertEqual(r["subject"], "Python Programming")

    # -------------------------------------------------------------------------
    # Scenario 9: Kannada questions and Kannada responses
    # -------------------------------------------------------------------------
    def test_scenario_9_kannada_questions_and_kannada_responses(self):
        """Verify Kannada questions are detected, system prompt specifies Kannada, and API returns Kannada."""
        kannada_query = "10ನೇ ತರಗತಿಯ ಗಣಿತ ಪರೀಕ್ಷೆಗೆ ಅಧ್ಯಯನ ಯೋಜನೆ ನೀಡಿ"
        self.assertTrue(assistant.is_in_domain(kannada_query))
        self.assertEqual(assistant.detect_language(kannada_query), "Kannada")

        # Test system prompt builder
        system_prompt = assistant.build_system_prompt([], query_language="Kannada")
        self.assertIn("KANNADA", system_prompt)
        self.assertIn("ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ", system_prompt)

        # Test API response with mocked Ollama Kannada generation
        mock_kannada_reply = "10ನೇ ತರಗತಿಯ ಗಣಿತ ಪರೀಕ್ಷೆಗಾಗಿ 7 ದಿನಗಳ ಅಧ್ಯಯನ ಯೋಜನೆ ಇಲ್ಲಿದೆ. ಪ್ರತಿದಿನ ಪ್ರಮೇಯಗಳು ಮತ್ತು ಸೂತ್ರಗಳನ್ನು ಅಭ್ಯಾಸ ಮಾಡಿ."
        mock_body = json.dumps({
            "model": "llama3.2:3b",
            "message": {"role": "assistant", "content": mock_kannada_reply},
            "done": True,
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_body
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = self.client.post("/api/chat", json={"message": kannada_query})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["language"], "Kannada")
            self.assertIn("ಅಧ್ಯಯನ ಯೋಜನೆ", data["reply"])

    # -------------------------------------------------------------------------
    # Scenario 10: English questions and English responses
    # -------------------------------------------------------------------------
    def test_scenario_10_english_questions_and_english_responses(self):
        """Verify English questions are detected, system prompt specifies English, and API returns English."""
        english_query = "Recommend 10th Standard Mathematics books."
        self.assertTrue(assistant.is_in_domain(english_query))
        self.assertEqual(assistant.detect_language(english_query), "English")

        # Test system prompt builder
        system_prompt = assistant.build_system_prompt([], query_language="English")
        self.assertIn("ENGLISH", system_prompt)

        # Test API response
        mock_english_reply = "For 10th Standard Mathematics, I recommend the NCERT / DSERT Class X textbook and R.S. Aggarwal."
        mock_body = json.dumps({
            "model": "llama3.2:3b",
            "message": {"role": "assistant", "content": mock_english_reply},
            "done": True,
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_body
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = self.client.post("/api/chat", json={"message": english_query})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["language"], "English")
            self.assertIn("NCERT", data["reply"])

    # -------------------------------------------------------------------------
    # Scenario 11: Unrelated questions rejected in both English and Kannada
    # -------------------------------------------------------------------------
    def test_scenario_11_unrelated_questions_rejected_in_english_and_kannada(self):
        """Verify unrelated questions (biryani, cricket, jokes) are strictly rejected in English & Kannada."""
        # English off-topic queries
        english_disallowed = [
            ("How do I cook biryani?", assistant.OUT_OF_DOMAIN_MESSAGE_EN),
            ("Who won yesterday's cricket match?", assistant.OUT_OF_DOMAIN_MESSAGE_EN),
            ("Tell me a funny joke.", assistant.OUT_OF_DOMAIN_MESSAGE_EN),
            ("Who is the prime minister of India?", assistant.OUT_OF_DOMAIN_MESSAGE_EN),
        ]

        # Kannada off-topic queries
        kannada_disallowed = [
            ("ಯಾವ ರೀತಿ ಬಿರಿಯಾನಿ ಮಾಡುವುದು?", assistant.OUT_OF_DOMAIN_MESSAGE_KN),
            ("ನಿನ್ನೆಯ ಕ್ರಿಕೆಟ್ ಪಂದ್ಯದಲ್ಲಿ ಯಾರು ಗೆದ್ದರು?", assistant.OUT_OF_DOMAIN_MESSAGE_KN),
            ("ನನಗೆ ಒಂದು ಹಾಸ್ಯ ಅಥವಾ ತಮಾಷೆ ಹೇಳಿ", assistant.OUT_OF_DOMAIN_MESSAGE_KN),
            ("ಕರ್ನಾಟಕದ ರಾಜಕೀಯ ಮತ್ತು ಚುನಾವಣೆ ಬಗ್ಗೆ ಹೇಳಿ", assistant.OUT_OF_DOMAIN_MESSAGE_KN),
        ]

        with patch("urllib.request.urlopen") as mock_urlopen:
            # Test English rejections
            for query, expected_msg in english_disallowed:
                with self.subTest(query=query, lang="en"):
                    self.assertFalse(assistant.is_in_domain(query))
                    res = self.client.post("/api/chat", json={"message": query})
                    self.assertEqual(res.status_code, 200)
                    data = res.get_json()
                    self.assertTrue(data["success"])
                    self.assertEqual(data["reply"], expected_msg)
                    self.assertEqual(data["recommended_resources"], [])

            # Test Kannada rejections
            for query, expected_msg in kannada_disallowed:
                with self.subTest(query=query, lang="kn"):
                    self.assertFalse(assistant.is_in_domain(query))
                    res = self.client.post("/api/chat", json={"message": query})
                    self.assertEqual(res.status_code, 200)
                    data = res.get_json()
                    self.assertTrue(data["success"])
                    self.assertEqual(data["reply"], expected_msg)
                    self.assertEqual(data["recommended_resources"], [])

            # Verify local Ollama was NEVER contacted for any disallowed queries
            mock_urlopen.assert_not_called()

    # -------------------------------------------------------------------------
    # Catalogue Honesty & Distinction Test
    # -------------------------------------------------------------------------
    def test_unmatched_catalogue_topic_returns_honest_note(self):
        """Verify topics without matching books return empty list and honest catalogue note."""
        unmatched_academic_query = "Can you recommend books on French history for 7th standard?"
        self.assertTrue(assistant.is_in_domain(unmatched_academic_query))

        # Must NOT return unrelated books (e.g. computer science or math books)
        resources = assistant.find_relevant_resources(unmatched_academic_query)
        self.assertEqual(resources, [], "Must return empty list for books not in library catalogue")

        # In response, catalogue_note must clearly state no books are available
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_body = json.dumps({
                "model": "llama3.2:3b",
                "message": {
                    "role": "assistant",
                    "content": "No matching books are currently available in our catalogue. However, for 7th standard French history, the key topics are..."
                },
                "done": True,
            }).encode("utf-8")
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_body
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            res = self.client.post("/api/chat", json={"message": unmatched_academic_query})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["recommended_resources"], [])
            self.assertEqual(data["catalogue_note"], assistant.NO_MATCHING_BOOKS_NOTE_EN)


class TestResourceOpeningAndDetails(unittest.TestCase):
    """
    Automated test suite verifying the resource-opening and book details functionality:
    - Books with verified external URLs (including Biology Class XII and Head First Java)
    - Books without external URLs (in-library physical collections)
    - Full publisher metadata support
    - GET /api/resources/<id> endpoint
    - Frontend modal structure
    """

    def setUp(self):
        self.client = app.test_client()
        seed_database()

    def test_get_single_resource_by_id_endpoint(self):
        """Verify GET /api/resources/<id> returns complete metadata including publisher and URL."""
        # Test valid ID 1
        res = self.client.get("/api/resources/1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        resource = data["resource"]
        self.assertEqual(resource["id"], 1)
        self.assertIn("title", resource)
        self.assertIn("author", resource)
        self.assertIn("publisher", resource)
        self.assertIn("subject", resource)
        self.assertIn("education_level", resource)
        self.assertIn("level", resource)
        self.assertIn("description", resource)
        self.assertIn("url", resource)

        # Test non-existent ID
        res_404 = self.client.get("/api/resources/99999")
        self.assertEqual(res_404.status_code, 404)
        data_404 = res_404.get_json()
        self.assertIn("error", data_404)

    def test_publisher_column_present_and_persisted(self):
        """Verify publisher is stored in database and returned in search queries."""
        all_resources = search_resources()
        self.assertGreater(len(all_resources), 0)
        for r in all_resources:
            self.assertIn("publisher", r, f"Resource {r['id']} must contain publisher key")
            self.assertTrue(r["publisher"] is not None, f"Resource {r['id']} publisher must not be None")

        # Test adding a resource with a publisher
        new_id = add_resource(
            title="Advanced Machine Learning Systems",
            author="Dr. Alice Smith",
            publisher="Cambridge University Press",
            subject="Artificial Intelligence",
            level="Advanced",
            education_level="Postgraduate",
            class_grade="MTech / PhD",
            department="Computer Science",
            language="English",
            description="Comprehensive guide to distributed machine learning systems.",
            resource_type="Book",
            url="https://example.edu/aml",
        )
        self.assertIsNotNone(new_id)
        saved = get_resource_by_id(new_id)
        self.assertEqual(saved["publisher"], "Cambridge University Press")

    def test_biology_textbook_url_preserved(self):
        """Verify the 2nd PUC Biology textbook URL is preserved and points to verified NCERT portal."""
        results = search_resources(query="Biology: Textbook for Class XII (2nd PUC Biology)")
        self.assertGreater(len(results), 0, "Must find Biology textbook")
        bio = results[0]
        self.assertEqual(bio["subject"], "Biology")
        self.assertEqual(bio["education_level"], "PUC")
        self.assertEqual(bio["class_grade"], "2nd PUC")
        self.assertTrue(bio["url"].startswith("https://ncert.nic.in/"), f"Biology URL must be verified NCERT: {bio['url']}")
        self.assertIn("lebo1", bio["url"])

    def test_head_first_java_has_verified_publisher_and_url(self):
        """Verify Head First Java has authentic publisher (O'Reilly Media) and verified URL."""
        results = search_resources(query="Head First Java")
        self.assertGreater(len(results), 0, "Must find Head First Java")
        hfj = results[0]
        self.assertEqual(hfj["title"], "Head First Java")
        self.assertEqual(hfj["publisher"], "O'Reilly Media")
        self.assertTrue(
            hfj["url"].startswith("https://www.oreilly.com/"),
            f"Head First Java must have official O'Reilly URL: {hfj['url']}"
        )

    def test_books_without_external_urls_support_details_action(self):
        """Verify in-library books without external URLs have complete metadata for details modal."""
        all_resources = search_resources()
        without_url = [r for r in all_resources if not r["url"] or not r["url"].strip()]
        self.assertGreater(len(without_url), 0, "Must have books representing physical library collections")

        # Check required fields for the book details popup
        for r in without_url:
            self.assertTrue(bool(r["title"]), f"Book {r['id']} must have a title")
            self.assertTrue(bool(r["author"]), f"Book {r['id']} must have an author")
            self.assertTrue(bool(r["publisher"]), f"Book {r['id']} must have a publisher: {r['title']}")
            self.assertTrue(bool(r["subject"]), f"Book {r['id']} must have a subject")
            self.assertTrue(bool(r["education_level"]), f"Book {r['id']} must have an educational level")
            self.assertTrue(bool(r["level"]), f"Book {r['id']} must have a difficulty level")
            self.assertTrue(bool(r["description"]), f"Book {r['id']} must have a description")

    def test_all_books_have_valid_opening_or_details_action(self):
        """Verify 100% of books in the catalogue have either a verified external URL or complete in-library details."""
        all_resources = search_resources()
        self.assertGreater(len(all_resources), 50, "Catalogue should contain complete book collection")

        for r in all_resources:
            url = (r.get("url") or "").strip()
            if url:
                # Must be a safe, legitimate HTTP or HTTPS link
                self.assertTrue(
                    url.startswith("http://") or url.startswith("https://"),
                    f"Resource {r['id']} ({r['title']}) has invalid URL scheme: {url}"
                )
            else:
                # Must have complete details for 'View Book Details' modal
                self.assertTrue(bool(r.get("title")), f"Resource {r['id']} must have title")
                self.assertTrue(bool(r.get("publisher")), f"Resource {r['id']} must have publisher")
                self.assertTrue(bool(r.get("description")), f"Resource {r['id']} must have description")

    def test_modal_structure_present_in_frontend(self):
        """Verify frontend index.html includes the Book Details modal dialog elements."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn('id="bookModalBackdrop"', html)
        self.assertIn('id="modalCloseBtn"', html)
        self.assertIn('id="modalBody"', html)
        self.assertIn('class="modal-dialog"', html)


if __name__ == "__main__":
    unittest.main()
