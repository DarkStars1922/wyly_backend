from unittest.mock import Mock, patch

from django.test import Client, TestCase, override_settings


class VRApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        response = self.client.get("/api/vr/config/")
        self.assertEqual(response.status_code, 200)
        self.csrf = response.json()["csrfToken"]

    def post(self, url, payload, csrf=True, **kwargs):
        headers = {"HTTP_X_CSRFTOKEN": self.csrf} if csrf else {}
        return self.client.post(url, data=payload, content_type="application/json", **headers, **kwargs)

    def create_session(self):
        response = self.post(
            "/api/vr/sessions/", {"consent": True, "companion": "xiaoxuan"}
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def submit_assessment(self, session_id, stage, responses=None):
        responses = responses or [1] * 20
        return self.post(
            f"/api/vr/sessions/{session_id}/assessments/",
            {"stage": stage, "responses": responses},
        )

    def submit_plan(self, session_id):
        response = self.post(
            f"/api/vr/sessions/{session_id}/recommendation/",
            {
                "goal": "relax",
                "instrument": "chinese",
                "tone": "jue",
                "soundscape": "rain",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_browser_posts_require_csrf_and_config_sets_cookie(self):
        response = self.client.post(
            "/api/vr/sessions/",
            data={"consent": True, "companion": "xiaoxuan"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        session = self.create_session()
        self.assertTrue(session)

    def test_session_isolation_and_history(self):
        session_id = self.create_session()
        other_client = Client()
        self.assertEqual(other_client.get(f"/api/vr/sessions/{session_id}/").status_code, 404)
        history = self.client.get("/api/vr/sessions/")
        self.assertEqual([row["id"] for row in history.json()["sessions"]], [session_id])

    def test_stai_scoring_and_missing_metrics_are_server_generated(self):
        session_id = self.create_session()
        response = self.submit_assessment(session_id, "before", [1] * 20)
        self.assertEqual(response.status_code, 200)
        assessment = response.json()
        self.assertEqual(assessment["questionnaire"]["score"], 50)
        self.assertEqual(assessment["questionnaire"]["scoringVersion"], "stai-s-v1")
        self.assertEqual(assessment["basic"], {
            "heartRate": None,
            "respiration": None,
            "temperature": None,
            "oxygenSaturation": None,
            "skinConductance": None,
        })
        self.assertTrue(all(value is None for value in assessment["device"].values()))
        self.assertFalse(assessment["flags"]["highRisk"])

    def test_malformed_questionnaire_is_rejected(self):
        session_id = self.create_session()
        for responses in ([1] * 19, [1] * 19 + [5], [True] * 20):
            response = self.submit_assessment(session_id, "before", responses)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get(f"/api/vr/sessions/{session_id}/").json()["before"], None)

    def test_recommendation_uses_current_questionnaire_and_playable_catalog(self):
        session_id = self.create_session()
        self.submit_assessment(session_id, "before", [4] * 20)
        plan = self.submit_plan(session_id)
        self.assertEqual(plan["sourceType"], "questionnaire")
        self.assertEqual(plan["algorithm"], "stai-questionnaire-catalog-v1")
        self.assertTrue(plan["videoId"].startswith("vr-video-"))
        self.assertTrue(plan["videoUrl"].startswith("/static/vr/"))
        self.assertNotIn("sampleId", plan)

        mismatch = self.post(
            f"/api/vr/sessions/{session_id}/experience/",
            {"event": "start", "duration": 120, "videoId": "arbitrary"},
        )
        self.assertEqual(mismatch.status_code, 400)

    def test_device_api_is_disabled_without_key(self):
        session_id = self.create_session()
        response = self.client.post(
            "/api/vr/device-assessments/",
            data={"sessionId": session_id, "stage": "before"},
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer anything",
        )
        self.assertEqual(response.status_code, 503)

    @override_settings(VR_AI_API_KEY="test-key", VR_AI_BASE_URL="https://ai.example.test")
    @patch("vr_healing.views.requests.post")
    def test_ai_success_is_cached_and_think_tags_are_removed(self, post):
        session_id = self.create_session()
        self.submit_assessment(session_id, "before", [1] * 20)
        self.submit_plan(session_id)
        self.submit_assessment(session_id, "after", [2] * 20)
        upstream = Mock(status_code=200)
        upstream.json.return_value = {
            "choices": [{"message": {"content": "<think>hidden</think>完成了舒缓记录。"}}]
        }
        post.return_value = upstream

        first = self.post(f"/api/vr/sessions/{session_id}/analysis/", {})
        second = self.post(f"/api/vr/sessions/{session_id}/analysis/", {})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["analysis"]["status"], "ready")
        self.assertEqual(first.json()["analysis"]["text"], "完成了舒缓记录。")
        self.assertEqual(second.json()["analysis"], first.json()["analysis"])
        self.assertEqual(post.call_count, 1)
        sent = post.call_args.kwargs["json"]
        self.assertNotIn(session_id, str(sent))
        self.assertEqual(sent["max_tokens"], 300)

    @override_settings(VR_AI_API_KEY="test-key", VR_AI_BASE_URL="https://ai.example.test")
    @patch("vr_healing.views.requests.post")
    def test_ai_failure_is_distinguished_and_cached(self, post):
        session_id = self.create_session()
        self.submit_assessment(session_id, "before")
        self.submit_plan(session_id)
        self.submit_assessment(session_id, "after")
        post.side_effect = RuntimeError("upstream detail must stay private")

        first = self.post(f"/api/vr/sessions/{session_id}/analysis/", {})
        second = self.post(f"/api/vr/sessions/{session_id}/analysis/", {})
        self.assertEqual(first.json()["analysis"], {"status": "failed"})
        self.assertEqual(second.json()["analysis"], {"status": "failed"})
        self.assertEqual(post.call_count, 1)

    @override_settings(VR_DEVICE_API_KEY="device-key")
    def test_device_payload_is_capped_and_scoped_to_exact_session(self):
        session_id = self.create_session()
        response = self.client.post(
            "/api/vr/device-assessments/",
            data={
                "sessionId": session_id,
                "stage": "before",
                "basic": {"heartRate": 72},
                "device": {"eyeX": 0.46},
                "series": {"heartRate": [72, 72.2]},
            },
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer device-key",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["assessment"]["basic"]["heartRate"], 72)
        self.assertEqual(response.json()["assessment"]["device"]["eyeX"], 0.46)
        too_long = self.client.post(
            "/api/vr/device-assessments/",
            data={"sessionId": session_id, "stage": "before", "series": {"heartRate": [1] * 1001}},
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer device-key",
        )
        self.assertEqual(too_long.status_code, 400)
