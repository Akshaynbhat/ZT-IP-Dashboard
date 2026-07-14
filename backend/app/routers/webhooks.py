import hmac
import hashlib
import uuid
import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.config import settings
from app.models.user import User
from app.models.access_log import AccessLog
from app.worker.scheduled_scoring import run_scoring_cycle


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"]
)

# Helper to verify GitHub HMAC signature
async def verify_github_signature(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed X-Hub-Signature-256 header"
        )
    
    body = await request.body()
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    actual = signature.split("sha256=")[1]
    if not hmac.compare_digest(actual, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub signature verification failed"
        )

# Helper to verify GitLab secret token
async def verify_gitlab_token(request: Request):
    token = request.headers.get("X-Gitlab-Token")
    if not token or token != settings.GITLAB_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Gitlab-Token"
        )

# Helper to resolve or auto-provision User based on Git credentials
def resolve_git_user(username: str, email: str, db: Session) -> User:
    # Attempt lookup by email or username
    user = db.query(User).filter(
        (User.email.ilike(email)) | (User.username.ilike(username))
    ).first()
    
    if not user:
        # Auto-provision Git user under default organization
        default_tenant = uuid.UUID("9f9bbf10-e3f3-470b-85be-587265bf02ab")
        user = User(
            id=uuid.uuid4(),
            keycloak_sub=f"git_{username}",
            username=username,
            email=email,
            role="employee",
            department="Engineering",
            tenant_id=default_tenant
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Auto-provisioned User identity for Git user: {username} ({email})")
    
    return user

@router.post("/github", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_github_signature)])
async def github_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ingest webhook events from GitHub, verifying payload signature.
    Maps repo pushes, clones/downloads, and branch changes to user access logs.
    """
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "push")
    
    repo_name = payload.get("repository", {}).get("name", "unknown-repo")
    sender_name = payload.get("sender", {}).get("login", "unknown-sender")
    sender_email = f"{sender_name}@github.com"
    
    # Map common webhook actions
    bytes_transferred = 0
    mapped_type = "repo_access"
    resource = repo_name
    
    if event_type == "push":
        commits = payload.get("commits", [])
        if commits:
            author = commits[0].get("author", {})
            sender_name = author.get("username") or author.get("name") or sender_name
            sender_email = author.get("email") or sender_email
            
        # Synthesize transfer size from commit counts
        bytes_transferred = len(commits) * 45000  # Approx 45KB per commit
        resource = f"{repo_name}/branches/{payload.get('ref', 'refs/heads/main').split('/')[-1]}"
        logger.info(f"GitHub Push Webhook: {sender_name} pushed {len(commits)} commits to {repo_name}")
        
    elif event_type in ("create", "delete"):
        ref_type = payload.get("ref_type")
        ref_name = payload.get("ref")
        mapped_type = "privilege_change" if ref_type == "branch" and event_type == "delete" else "repo_access"
        resource = f"{repo_name}/{ref_type}/{ref_name}"
        logger.info(f"GitHub Branch/Tag Webhook: {sender_name} {event_type}d {ref_type} {ref_name} on {repo_name}")
        
    user = resolve_git_user(sender_name, sender_email, db)
    
    # Ingest access log
    log = AccessLog(
        user_id=user.id,
        device_id=None,  # Webhooks occur server-to-server
        event_type=mapped_type,
        resource=resource,
        bytes_transferred=bytes_transferred,
        ip_address=request.client.host if request.client else "127.0.0.1",
        location="GitHub Webhook",
        tenant_id=user.tenant_id
    )
    db.add(log)
    db.commit()
    
    background_tasks.add_task(run_scoring_cycle)
    
    return {"message": "GitHub event accepted", "log_id": str(log.id)}


@router.post("/gitlab", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_gitlab_token)])
async def gitlab_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ingest webhook events from GitLab, verifying token credentials.
    """
    payload = await request.json()
    object_kind = payload.get("object_kind", "push")
    
    project = payload.get("project", {})
    repo_name = project.get("name") or project.get("path_with_namespace") or "unknown-repo"
    
    sender_name = payload.get("user_username") or payload.get("user_name") or "unknown-sender"
    sender_email = payload.get("user_email") or f"{sender_name}@gitlab.com"
    
    bytes_transferred = 0
    mapped_type = "repo_access"
    resource = repo_name
    
    if object_kind == "push":
        commits = payload.get("commits", [])
        if commits:
            author = commits[0].get("author", {})
            sender_name = author.get("name") or sender_name
            sender_email = author.get("email") or sender_email
            
        bytes_transferred = len(commits) * 45000
        ref_branch = payload.get("ref", "refs/heads/main").split('/')[-1]
        resource = f"{repo_name}/branches/{ref_branch}"
        logger.info(f"GitLab Push Webhook: {sender_name} pushed {len(commits)} commits to {repo_name}")
        
    user = resolve_git_user(sender_name, sender_email, db)
    
    log = AccessLog(
        user_id=user.id,
        device_id=None,
        event_type=mapped_type,
        resource=resource,
        bytes_transferred=bytes_transferred,
        ip_address=request.client.host if request.client else "127.0.0.1",
        location="GitLab Webhook",
        tenant_id=user.tenant_id
    )
    db.add(log)
    db.commit()
    
    background_tasks.add_task(run_scoring_cycle)
    
    return {"message": "GitLab event accepted", "log_id": str(log.id)}

