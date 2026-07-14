import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
import redis.asyncio as aioredis
from app.config import settings
from app.auth.keycloak import validate_token, get_token_roles, get_token_sub

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

class ConnectionManager:
    def __init__(self):
        # Maps websocket connection to user metadata: {websocket: {"sub": user_id, "roles": [...]}}
        self.active_connections = {}
        self.redis_client = None
        self.pubsub_task = None

    async def initialize(self):
        """Initializes Redis connection and starts background Pub/Sub listener."""
        if not self.redis_client:
            self.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            self.pubsub_task = asyncio.create_task(self._redis_listener())
            logger.info("WebSocket ConnectionManager initialized with Redis Pub/Sub.")

    async def connect(self, websocket: WebSocket, user_info: dict):
        await websocket.accept()
        self.active_connections[websocket] = user_info
        logger.info(f"WebSocket client connected: sub={user_info['sub']}, roles={user_info['roles']}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            user_info = self.active_connections.pop(websocket)
            logger.info(f"WebSocket client disconnected: sub={user_info['sub']}")

    async def _redis_listener(self):
        """Background task that subscribes to Redis updates and dispatches them to connections."""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("zt_updates")
        logger.info("Subscribed to Redis channel: zt_updates")
        
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    try:
                        data = json.loads(message["data"])
                        await self.dispatch_update(data)
                    except Exception as e:
                        logger.error(f"Error parsing pub/sub message: {str(e)}")
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub listener task cancelled.")
        except Exception as e:
            logger.error(f"Redis Pub/Sub listener crashed: {str(e)}")
            # Retry initialization after delay
            await asyncio.sleep(5)
            self.pubsub_task = asyncio.create_task(self._redis_listener())

    async def dispatch_update(self, data: dict):
        """Dispatches real-time update payloads to authorized WebSocket connections."""
        event_user_id = data.get("user_id")
        if not event_user_id:
            return

        dead_connections = []
        for ws, info in self.active_connections.items():
            try:
                # Zero Trust checks:
                # Admins and analysts receive all security telemetry.
                # Standard employees only receive updates related to their own identity.
                is_staff = "admin" in info["roles"] or "analyst" in info["roles"]
                is_self = info["sub"] == event_user_id
                
                if is_staff or is_self:
                    await ws.send_json(data)
            except WebSocketDisconnect:
                dead_connections.append(ws)
            except Exception as e:
                logger.error(f"Failed to send websocket update: {str(e)}")
                dead_connections.append(ws)

        for ws in dead_connections:
            self.disconnect(ws)

    async def publish_update(self, update_type: str, user_id: str, payload: dict):
        """Helper to publish an update to Redis pub/sub from anywhere in the app."""
        if self.redis_client:
            message = {
                "type": update_type,
                "user_id": user_id,
                "data": payload
            }
            await self.redis_client.publish("zt_updates", json.dumps(message))

manager = ConnectionManager()

@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Keycloak JWT Authentication Token")
):
    """
    WebSocket endpoint for real-time security events.
    Requires authentication via token query parameter.
    """
    # 1. Authenticate WebSocket connection
    try:
        payload = await validate_token(token)
        user_info = {
            "sub": get_token_sub(payload),
            "roles": get_token_roles(payload)
        }
    except Exception as e:
        logger.warning(f"Rejecting WebSocket connection due to auth failure: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Accept and manage connection
    await manager.connect(websocket, user_info)
    
    # 3. Wait for client messages (heartbeat/pings) or disconnect
    try:
        while True:
            # We don't expect actual requests from clients, just keep connection open
            data = await websocket.receive_text()
            # If client sends a ping, echo it
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error on sub {user_info['sub']}: {str(e)}")
        manager.disconnect(websocket)
