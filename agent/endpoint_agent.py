import os
import sys
import time
import uuid
import json
import hashlib
import logging
import platform
import threading
import sqlite3
import requests
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("EndpointAgent")

# Load environment configuration
load_dotenv()

# System variables
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "zt-dashboard")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "backend-api")
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "zt_backend_secret")
AGENT_USERNAME = os.getenv("AGENT_USERNAME", "test.admin")
AGENT_PASSWORD = os.getenv("AGENT_PASSWORD", "Admin@123")

# Auto-generate dynamic device fingerprint using hardware context
def get_device_fingerprint() -> str:
    node = platform.node()
    system = platform.system()
    mac = str(uuid.getnode())
    raw = f"{node}-{system}-{mac}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

DEVICE_FINGERPRINT = get_device_fingerprint()
OS_PLATFORM = platform.system()

# User ID representing the logged-in operator (defaulting to reproducible UUID)
USER_ID = os.getenv("USER_ID", str(uuid.uuid5(uuid.NAMESPACE_DNS, "alice.dev")))

# Local SQLite Offline Cache Manager
class EventCache:
    def __init__(self, db_path="agent_cache.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def cache_event(self, event_type: str, resource: str, bytes_transferred: int, ip: str, location: str, extra: dict = None):
        payload = {
            "user_id": USER_ID,
            "device_fingerprint": DEVICE_FINGERPRINT,
            "event_type": event_type,
            "resource": resource,
            "bytes_transferred": bytes_transferred,
            "ip_address": ip,
            "location": location,
            "os": OS_PLATFORM
        }
        if extra:
            payload.update(extra)
            
        event_id = str(uuid.uuid4())
        with self.conn:
            self.conn.execute(
                "INSERT INTO events (id, payload, created_at) VALUES (?, ?, ?)",
                (event_id, json.dumps(payload), time.time())
            )
        logger.info(f"Cached local event: {event_type} -> {resource}")

    def get_unsent_events(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, payload FROM events ORDER BY created_at ASC")
        return cursor.fetchall()

    def remove_event(self, event_id: str):
        with self.conn:
            self.conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

# Initialize local cache database
cache = EventCache()

# Keycloak Token Management Client
class AuthTokenProvider:
    def __init__(self):
        self.token = None
        self.expires_at = 0

    def get_token(self) -> str:
        if self.token and time.time() < self.expires_at - 10:
            return self.token
            
        token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "username": AGENT_USERNAME,
            "password": AGENT_PASSWORD
        }
        try:
            res = requests.post(token_url, data=data, timeout=5)
            res.raise_for_status()
            res_json = res.json()
            self.token = res_json["access_token"]
            self.expires_at = time.time() + res_json.get("expires_in", 300)
            logger.info("Successfully fetched new OIDC authentication token.")
            return self.token
        except Exception as e:
            logger.error(f"Failed to authenticate with Keycloak: {str(e)}")
            return None

auth_provider = AuthTokenProvider()

# Heartbeat Sender Task
def run_heartbeat_loop():
    while True:
        try:
            cache.cache_event(
                event_type="login",
                resource="endpoint-agent-heartbeat",
                bytes_transferred=0,
                ip="127.0.0.1",
                location="Local Workspace",
                extra={"status": "running"}
            )
        except Exception as e:
            logger.error(f"Error caching heartbeat: {str(e)}")
        time.sleep(300)  # Heartbeat every 5 minutes

# File Change Watchdog Handler
class FileWatchHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Log modifications for source code and asset files
        filepath = event.src_path
        if filepath.endswith((".py", ".ts", ".tsx", ".js", ".json", ".zip", ".tar.gz")):
            try:
                filesize = os.path.getsize(filepath)
                cache.cache_event(
                    event_type="file_download", # Ingested as file interactions
                    resource=os.path.basename(filepath),
                    bytes_transferred=filesize,
                    ip="127.0.0.1",
                    location="Local Workspace",
                    extra={"filepath": filepath}
                )
            except Exception as e:
                logger.error(f"Error handling modified file: {str(e)}")

# Process connection monitor using psutil
def run_process_monitor():
    seen_pids = set(psutil.pids())
    while True:
        try:
            current_pids = set(psutil.pids())
            new_pids = current_pids - seen_pids
            for pid in new_pids:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name().lower()
                    
                    # Highlight critical actions matching developer tool activities
                    is_suspicious_proc = any(kw in proc_name for kw in ["git", "docker", "python", "curl", "ssh"])
                    if is_suspicious_proc:
                        cache.cache_event(
                            event_type="repo_access",
                            resource=f"proc:{proc_name}",
                            bytes_transferred=0,
                            ip="127.0.0.1",
                            location="Local System",
                            extra={"pid": pid, "cmdline": " ".join(proc.cmdline())}
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            seen_pids = current_pids
        except Exception as e:
            logger.error(f"Process monitor error: {str(e)}")
        time.sleep(2)

# Dynamic USB Removable Storage Mount Monitor
def run_usb_monitor():
    existing_partitions = set(p.mountpoint for p in psutil.disk_partitions())
    while True:
        try:
            current_partitions = set(p.mountpoint for p in psutil.disk_partitions())
            new_mounts = current_partitions - existing_partitions
            for mount in new_mounts:
                cache.cache_event(
                    event_type="privilege_change", # Flag device mount changes
                    resource=f"mount:{mount}",
                    bytes_transferred=0,
                    ip="127.0.0.1",
                    location="Local Device Mount",
                    extra={"mountpoint": mount}
                )
                logger.warning(f"Removable storage partition mount detected at: {mount}")
            existing_partitions = current_partitions
        except Exception as e:
            logger.error(f"USB drive monitor error: {str(e)}")
        time.sleep(5)

# Network connection port telemetry
def run_network_monitor():
    seen_connections = set()
    while True:
        try:
            conns = psutil.net_connections(kind="inet")
            for c in conns:
                # Target outgoing connections in ESTABLISHED state
                if c.status == "ESTABLISHED" and c.raddr:
                    conn_key = f"{c.raddr.ip}:{c.raddr.port}"
                    if conn_key not in seen_connections:
                        seen_connections.add(conn_key)
                        
                        # Identify connections to external ports
                        if c.raddr.port in (22, 443, 80, 8080):
                            cache.cache_event(
                                event_type="repo_access",
                                resource=f"net:{conn_key}",
                                bytes_transferred=0,
                                ip=c.raddr.ip,
                                location="Remote Connection",
                                extra={"fd": c.fd, "family": c.family}
                            )
            # Cap cached size
            if len(seen_connections) > 1000:
                seen_connections.clear()
        except Exception as e:
            logger.error(f"Network connections monitor error: {str(e)}")
        time.sleep(10)

# Offline Cache Sync Dispatcher with retry mechanisms
def run_cache_dispatcher():
    backoff_seconds = 5
    while True:
        try:
            unsent = cache.get_unsent_events()
            if not unsent:
                time.sleep(5)
                continue
                
            token = auth_provider.get_token()
            if not token:
                logger.warning("No authentication token available. Delaying sync...")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 300)
                continue

            # Reset backoff on token recovery
            backoff_seconds = 5

            for event_id, payload in unsent:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                event_data = json.loads(payload)
                try:
                    url = f"{BASE_URL}/api/v1/events"
                    res = requests.post(url, json=event_data, headers=headers, timeout=5)
                    if res.status_code == 202:
                        cache.remove_event(event_id)
                        logger.info(f"Transmitted cached event successfully: {event_id}")
                    else:
                        logger.warning(f"Ingestion rejected event: code={res.status_code}")
                except requests.RequestException as e:
                    logger.error(f"Server transmission failure: {str(e)}. Retrying later...")
                    break
        except Exception as e:
            logger.error(f"Cache dispatcher cycle error: {str(e)}")
        time.sleep(5)

# Main Application Entry Point
def main():
    logger.info("Initializing Zero Trust Endpoint Security Monitoring Agent...")
    logger.info(f"Fingerprint: {DEVICE_FINGERPRINT} | Reporting under Operator: {USER_ID}")

    # Watch folder (current repo directory)
    watch_path = os.getcwd()

    # 1. Start Watchdog File System Observer
    event_handler = FileWatchHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watch_path, recursive=True)
    observer.start()
    logger.info(f"Filesystem observer watching: {watch_path}")

    # 2. Start background worker telemetry loops
    threads = [
        threading.Thread(target=run_process_monitor, daemon=True, name="ProcMonitor"),
        threading.Thread(target=run_usb_monitor, daemon=True, name="USBMonitor"),
        threading.Thread(target=run_network_monitor, daemon=True, name="NetMonitor"),
        threading.Thread(target=run_heartbeat_loop, daemon=True, name="Heartbeat"),
        threading.Thread(target=run_cache_dispatcher, daemon=True, name="CacheDispatcher")
    ]

    for t in threads:
        t.start()
        logger.info(f"Worker thread started: {t.name}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Termination signal caught. Stopping observer...")
        observer.stop()
    observer.join()
    logger.info("Endpoint Security Agent shut down successfully.")

if __name__ == "__main__":
    main()
