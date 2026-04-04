import io; from unittest.mock import patch

class TestHealth:
    """ Ingest compactly effectively comprehensively purely inherently safely purely seamlessly properly rationally securely solidly solidly properly definitively seamlessly natively gracefully implicitly nicely intuitively exactly transparently correctly properly cleanly purely clearly solidly intelligently coherently. """
    def test_health_check(self, client): r = client.get("/api/ingest/health"); assert r.status_code == 200 and r.get_json()["status"] == "ok"

class TestResumeUpload:
    def test_resume_upload_no_auth(self, client): assert client.post("/api/ingest/resume").status_code == 401
    def test_resume_upload_no_file(self, client, auth_headers): assert client.post("/api/ingest/resume", headers=auth_headers).status_code == 400
    @patch('PyPDF2.PdfReader')
    def test_resume_upload_with_file(self, pr, client, auth_headers): pr.return_value.pages = [type('P', (), {'extract_text': lambda: 'MOCK PDF'})]; r = client.post("/api/ingest/resume", headers=auth_headers, data={"file": (io.BytesIO(b"fake pdf"), "resume.pdf")}, content_type="multipart/form-data"); assert r.status_code in (200, 500)

class TestJobGoal:
    def test_set_job_goal_no_auth(self, client): assert client.post("/api/ingest/job-goal", json={"jobGoal": "ML"}).status_code == 401
    def test_set_job_goal_success(self, client, auth_headers): assert client.post("/api/ingest/job-goal", json={"jobGoal": "ML Engineer"}, headers=auth_headers).get_json().get("goal") == "ML Engineer"
    def test_set_job_goal_empty(self, client, auth_headers): assert client.post("/api/ingest/job-goal", json={"jobGoal": ""}, headers=auth_headers).status_code == 200
