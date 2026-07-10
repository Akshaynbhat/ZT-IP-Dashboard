import os
import sys
import time
import uuid
import random
import argparse
from datetime import datetime, timedelta
import requests
import psycopg2

# Base configurations
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = "zt-dashboard"
CLIENT_ID = "backend-api"
CLIENT_SECRET = "zt_backend_secret"

# Persona declarations (using reproducible uuid5)
USERS = [
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "alice.dev")), "name": "alice.dev", "department": "Engineering", "role": "employee"},
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "bob.dev")), "name": "bob.dev", "department": "Engineering", "role": "employee"},
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "charlie.ops")), "name": "charlie.ops", "department": "DevOps", "role": "employee"},
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "diana.sec")), "name": "diana.sec", "department": "Security", "role": "analyst"},
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "eve.insider")), "name": "eve.insider", "department": "Engineering", "role": "employee"},
]

# Asset names
REPOS = ["payments-core", "auth-library", "api-gateway", "frontend-portal"]
SUSPICIOUS_REPOS = ["customer-pii-db", "financial-ledger", "payroll-records", "compliance-audits"]

# Helper class for Keycloak Token Refresh Management
class TokenManager:
    def __init__(self):
        self.token = None
        self.expires_at = 0

    def get_token(self):
        if self.token and time.time() < self.expires_at - 10:
            return self.token
        
        # Token needs to be refreshed
        token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "username": "test.admin",
            "password": "Admin@123"
        }
        res = requests.post(token_url, data=data, timeout=10)
        res.raise_for_status()
        res_json = res.json()
        self.token = res_json["access_token"]
        self.expires_at = time.time() + res_json.get("expires_in", 300)
        return self.token

token_manager = TokenManager()

def seed_database_users():
    """
    Direct PostgreSQL seeding to ensure simulated persona UUIDs exist inside the database user mapping tables.
    """
    print("Connecting to database to verify/seed simulation user accounts...")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "zt_dashboard")
    db_user = os.getenv("DB_USER", "zt_admin")
    db_pass = os.getenv("DB_PASSWORD", "zt_pass")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_pass
        )
        cur = conn.cursor()
        for u in USERS:
            cur.execute("""
                INSERT INTO users (id, username, email, role, department, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO NOTHING;
            """, (u["id"], u["name"], f"{u['name']}@zt-enterprise.io", u["role"], u["department"]))
        conn.commit()
        cur.close()
        conn.close()
        print("Database user accounts verified and seeded successfully.")
    except Exception as e:
        print(f"Warning: Database user seeding failed: {e}")
        print("Continuing simulation. Make sure users exist or endpoints allow dynamic auto-provisioning.")

# Event generators
def make_normal_event(user):
    username = user["name"]
    event_type = random.choice(["login", "repo_access", "file_download"])
    
    # Base event data
    event = {
        "user_id": user["id"],
        "device_fingerprint": f"{username}-laptop-001",
        "ip_address": f"10.0.0.{random.randint(10, 250)}",
        "location": "Bengaluru, IN",
        "bytes_transferred": 0,
        "event_type": event_type
    }

    if event_type == "login":
        event["resource"] = "okta-auth"
    elif event_type == "repo_access":
        event["resource"] = random.choice(REPOS)
    elif event_type == "file_download":
        event["resource"] = f"{random.choice(REPOS)}/src/main.py"
        event["bytes_transferred"] = random.randint(102400, 819200) # 100KB-800KB
        
    return event

def make_suspicious_event(user):
    event_type = random.choice(["login", "repo_access", "file_download", "privilege_change", "code_export"])
    
    # Suspicious characteristics: off-hours, external IP, random device fingerprint
    event = {
        "user_id": user["id"],
        "device_fingerprint": str(uuid.uuid4())[:18], # Unknown new device
        "ip_address": random.choice(["185.220.101.5", "194.165.16.22", "82.102.23.45"]),
        "location": "Unknown / TOR Exit Node",
        "bytes_transferred": 0,
        "event_type": event_type
    }

    if event_type == "login":
        event["resource"] = "identity-provider-admin"
    elif event_type == "repo_access":
        event["resource"] = random.choice(SUSPICIOUS_REPOS)
    elif event_type == "file_download":
        event["resource"] = f"{random.choice(SUSPICIOUS_REPOS)}/full-database-dump.zip"
        event["bytes_transferred"] = random.randint(150000000, 950000000) # 150MB-950MB
    elif event_type == "privilege_change":
        event["resource"] = "active-directory-admin-group"
    elif event_type == "code_export":
        event["resource"] = "proprietary-payments-logic"

    return event

def send_event(event, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/api/v1/events"
    res = requests.post(url, json=event, headers=headers, timeout=5)
    res.raise_for_status()
    return res.json()

def main():
    parser = argparse.ArgumentParser(description="Zero Trust Explanable AI Insider Threat Simulator")
    parser.add_argument("--scenario", choices=["normal", "suspicious", "mixed"], default="mixed", help="Type of events to simulate")
    parser.add_argument("--users", type=int, default=5, help="Number of simulated users (max 5)")
    parser.add_argument("--duration", type=int, default=10, help="Simulation runtime duration in minutes")
    parser.add_argument("--interval", type=int, default=5, help="Interval sleep seconds between events")
    
    args = parser.parse_args()
    
    # Cap simulated users to length of seeded personas
    num_users = min(max(1, args.users), len(USERS))
    sim_users = USERS[:num_users]
    
    # Seed DB
    seed_database_users()
    
    # Calculate end time
    end_time = datetime.now() + timedelta(minutes=args.duration)
    
    print(f"\n==========================================")
    print(f"Starting Simulator:")
    print(f"  - Scenario: {args.scenario.upper()}")
    print(f"  - Target Users count: {len(sim_users)}")
    print(f"  - Runtime: {args.duration} minute(s)")
    print(f"  - Send Interval: {args.interval} second(s)")
    print(f"==========================================\n")

    total_sent = 0
    normal_sent = 0
    suspicious_sent = 0

    try:
        while datetime.now() < end_time:
            # 1. Fetch valid Keycloak Token
            try:
                token = token_manager.get_token()
            except Exception as e:
                print(f"Error requesting Keycloak authorization token: {e}")
                time.sleep(5)
                continue

            # 2. Select User
            selected_user = random.choice(sim_users)
            is_suspicious_draw = False

            if args.scenario == "suspicious":
                is_suspicious_draw = True
            elif args.scenario == "mixed":
                # In mixed scenario, eve.insider is the malicious persona
                if selected_user["name"] == "eve.insider":
                    is_suspicious_draw = True
                else:
                    # Very small chance for other users to behave suspiciously
                    is_suspicious_draw = random.random() < 0.05

            # 3. Build Event Data
            if is_suspicious_draw:
                event = make_suspicious_event(selected_user)
                tag = "SUSPICIOUS"
                suspicious_sent += 1
            else:
                event = make_normal_event(selected_user)
                tag = "normal"
                normal_sent += 1

            # 4. Transmit Event to Ingestion API
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                res = send_event(event, token)
                print(f"[{timestamp_str}] SENT: {selected_user['name']} | {event['event_type']} | {event['resource']} | {event['ip_address']} | {tag.upper()}")
                total_sent += 1
            except Exception as e:
                print(f"[{timestamp_str}] FAILED to transmit event for {selected_user['name']}: {e}")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nSimulation aborted by user control.")

    print(f"\n==========================================")
    print(f"=== SIMULATION COMPLETE ===")
    print(f"Events sent: {total_sent}")
    print(f"Normal events: {normal_sent}")
    print(f"Suspicious events: {suspicious_sent}")
    print(f"Check dashboard at http://localhost:3000 for trust score changes")
    print(f"==========================================\n")

if __name__ == "__main__":
    main()
