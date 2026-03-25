import io


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/api/ingest/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestResumeUpload:
    def test_resume_upload_no_auth(self, client):
        resp = client.post("/api/ingest/resume")
        assert resp.status_code == 401

    def test_resume_upload_no_file(self, client, auth_headers):
        resp = client.post("/api/ingest/resume", headers=auth_headers)
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_resume_upload_with_file(self, client, auth_headers):
        fake_pdf = (io.BytesIO(b"fake pdf content"), "resume.pdf")
        resp = client.post(
            "/api/ingest/resume",
            headers=auth_headers,
            data={"file": fake_pdf},
            content_type="multipart/form-data"
        )
        assert resp.status_code == 200
        assert "extracted_text" in resp.get_json()


class TestJobGoal:
    def test_set_job_goal_no_auth(self, client):
        resp = client.post("/api/ingest/job-goal", json={"jobGoal": "ML Engineer"})
        assert resp.status_code == 401

    def test_set_job_goal_success(self, client, auth_headers):
        resp = client.post("/api/ingest/job-goal", json={"jobGoal": "ML Engineer"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["goal"] == "ML Engineer"

    def test_set_job_goal_empty(self, client, auth_headers):
        resp = client.post("/api/ingest/job-goal", json={"jobGoal": ""}, headers=auth_headers)
        assert resp.status_code == 200
