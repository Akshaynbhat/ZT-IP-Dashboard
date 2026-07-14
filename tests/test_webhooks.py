import hmac
import hashlib
import json
import unittest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings
from app.dependencies import get_db
from app.db.session import Base
from app.models.user import User
from app.models.access_log import AccessLog
from app.models.organization import Organization

# Configure isolated in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override FastAPI's database dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Patch background worker's SessionLocal to prevent connecting to real Postgres during testing
import app.worker.scheduled_scoring as worker_module
worker_module.SessionLocal = TestingSessionLocal



class TestWebhooks(unittest.TestCase):
    def setUp(self):
        # Create all tables in the temporary in-memory database
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.client = TestClient(app)
        
        # Seed the default organization required by foreign keys
        default_org_id = uuid.UUID("9f9bbf10-e3f3-470b-85be-587265bf02ab")
        org = Organization(id=default_org_id, name="Default Organization")
        self.db.add(org)
        self.db.commit()
        
        self.test_username = "git_tester"
        self.test_email = "tester@git-integration.test"

    def tearDown(self):
        self.db.close()
        # Drop all tables to isolate test cases
        Base.metadata.drop_all(bind=engine)

    def test_github_webhook_invalid_signature(self):
        payload = {"repository": {"name": "test-repo"}, "sender": {"login": self.test_username}}
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": "sha256=invalidsignature"
        }
        res = self.client.post("/api/v1/webhooks/github", json=payload, headers=headers)
        self.assertEqual(res.status_code, 401)

    def test_github_webhook_valid_signature_push(self):
        payload = {
            "repository": {"name": "financial-services"},
            "sender": {"login": self.test_username},
            "ref": "refs/heads/feature-x",
            "commits": [
                {"id": "c1", "message": "Add payment processing gateway", "author": {"name": self.test_username, "email": self.test_email}}
            ]
        }
        body_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json"
        }
        
        res = self.client.post("/api/v1/webhooks/github", content=body_bytes, headers=headers)
        self.assertEqual(res.status_code, 202)
        
        # Verify access log was created in DB
        db_user = self.db.query(User).filter(User.username == self.test_username).first()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.email, self.test_email)
        
        log = self.db.query(AccessLog).filter(AccessLog.user_id == db_user.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, "repo_access")
        self.assertIn("financial-services/branches/feature-x", log.resource)
        self.assertEqual(log.location, "GitHub Webhook")

    def test_gitlab_webhook_invalid_token(self):
        payload = {"project": {"name": "test-repo"}}
        headers = {"X-Gitlab-Token": "bad-token"}
        res = self.client.post("/api/v1/webhooks/gitlab", json=payload, headers=headers)
        self.assertEqual(res.status_code, 401)

    def test_gitlab_webhook_valid_token(self):
        payload = {
            "project": {"name": "core-ledger"},
            "user_username": self.test_username,
            "user_email": self.test_email,
            "object_kind": "push",
            "commits": [{"id": "g1", "author": {"name": self.test_username, "email": self.test_email}}]
        }
        headers = {
            "X-Gitlab-Token": settings.GITLAB_WEBHOOK_SECRET,
            "Content-Type": "application/json"
        }
        res = self.client.post("/api/v1/webhooks/gitlab", json=payload, headers=headers)
        self.assertEqual(res.status_code, 202)
        
        # Verify log entry in DB
        db_user = self.db.query(User).filter(User.username == self.test_username).first()
        self.assertIsNotNone(db_user)
        
        log = self.db.query(AccessLog).filter(AccessLog.user_id == db_user.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, "repo_access")
        self.assertIn("core-ledger", log.resource)
        self.assertEqual(log.location, "GitLab Webhook")

    def test_policy_enforcement_restrict(self):
        from app.models.policy_rule import PolicyRule
        from app.auth.rbac import get_current_user
        from fastapi import HTTPException

        # 1. Create a policy rule that restricts access for scores between 0.0 and 50.0
        rule = PolicyRule(
            id=uuid.uuid4(),
            rule_name="Restrict Low Scores",
            threshold_min=0.0,
            threshold_max=50.0,
            action="restrict",
            active=True
        )
        self.db.add(rule)
        
        # 2. Setup a standard employee user
        test_user = User(
            id=uuid.uuid4(),
            keycloak_sub="git_tester",
            username=self.test_username,
            email=self.test_email,
            role="employee",
            department="Engineering",
            tenant_id=uuid.UUID("9f9bbf10-e3f3-470b-85be-587265bf02ab")
        )
        self.db.add(test_user)
        self.db.commit()

        # 3. Simulate a webhook push event that will generate a low trust score (computed at ~32.27)
        payload = {
            "repository": {"name": "financial-services"},
            "sender": {"login": self.test_username},
            "ref": "refs/heads/feature-x",
            "commits": [
                {"id": "c1", "message": "Add payment processing gateway", "author": {"name": self.test_username, "email": self.test_email}}
            ]
        }
        body_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json"
        }
        
        res = self.client.post("/api/v1/webhooks/github", content=body_bytes, headers=headers)
        self.assertEqual(res.status_code, 202)

        # 4. Verify that calling get_current_user now raises 403 Forbidden due to active restriction policy!
        token_payload = {
            "sub": "git_tester",
            "preferred_username": self.test_username,
            "email": self.test_email,
            "resource_access": {settings.KEYCLOAK_CLIENT_ID: {"roles": ["employee"]}}
        }
        
        with self.assertRaises(HTTPException) as context:
            get_current_user(payload=token_payload, db=self.db)
        
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("Access restricted", context.exception.detail)

if __name__ == "__main__":
    unittest.main()

