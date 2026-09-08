"""Out-of-app (Expo) push notification delivery.

The whole push system lives in this file: storing a device's Expo push token,
fanning a message out to every registered device, cleaning up tokens Expo tells
us are dead, and the announcement broadcast that the notification controller
calls whenever a new update is created.

Nothing else in the codebase needs to know how push works -- callers only use
`broadcast_announcement` (or `send_to_all` / `send_to_users` for anything else).
"""

from typing import Any, Dict, List, Optional

from quart import current_app
from pymongo.results import UpdateResult

from nautilus_api.config import Config

# Expo's public push endpoint. Works without an access token unless the Expo
# project has "enhanced push security" turned on, in which case EXPO_TOKEN is
# required (see Config.EXPO_TOKEN).
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Expo accepts at most 100 messages per request.
EXPO_BATCH_SIZE = 100

# Notification bodies get truncated so the OS banner stays readable.
MAX_BODY_LENGTH = 178

# Errors Expo returns for a token that will never be deliverable again.
DEAD_TOKEN_ERRORS = {"DeviceNotRegistered", "InvalidCredentials"}


async def _get_collection(collection_name: str):
    """Helper to retrieve a MongoDB collection from the current app's database."""
    return current_app.db[collection_name]


def is_valid_expo_token(token: Any) -> bool:
    """Return True if `token` looks like an Expo push token."""
    if not isinstance(token, str):
        return False
    return token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken[")


# --------------------------------------------------------------------------- #
# Token storage
# --------------------------------------------------------------------------- #

async def save_device_token(user_id: int, token: str) -> UpdateResult:
    """Store (or replace) a user's Expo push token."""
    users = await _get_collection("users")
    return await users.update_one(
        {"_id": user_id},
        {"$set": {"notification_token": token}},
    )


async def remove_device_token(user_id: int) -> UpdateResult:
    """Forget a user's Expo push token (e.g. on logout)."""
    users = await _get_collection("users")
    return await users.update_one(
        {"_id": user_id},
        {"$unset": {"notification_token": ""}},
    )


async def get_device_tokens(exclude_user_id: Optional[int] = None) -> List[str]:
    """Every valid Expo push token we know about, optionally skipping one user."""
    users = await _get_collection("users")

    query: Dict[str, Any] = {"notification_token": {"$exists": True, "$ne": None}}
    if exclude_user_id is not None:
        query["_id"] = {"$ne": exclude_user_id}

    documents = await users.find(query, {"_id": 1, "notification_token": 1}).to_list(length=None)

    # De-duplicate: two accounts on one device would otherwise get two banners.
    tokens: List[str] = []
    for document in documents:
        token = document.get("notification_token")
        if is_valid_expo_token(token) and token not in tokens:
            tokens.append(token)

    return tokens


async def get_device_tokens_for_users(user_ids: List[int]) -> List[str]:
    """Expo push tokens for a specific set of users."""
    users = await _get_collection("users")

    documents = await users.find(
        {"_id": {"$in": user_ids}, "notification_token": {"$exists": True, "$ne": None}},
        {"_id": 1, "notification_token": 1},
    ).to_list(length=None)

    tokens: List[str] = []
    for document in documents:
        token = document.get("notification_token")
        if is_valid_expo_token(token) and token not in tokens:
            tokens.append(token)

    return tokens


async def _drop_dead_tokens(tokens: List[str]) -> None:
    """Unset tokens Expo reported as permanently undeliverable."""
    if not tokens:
        return

    users = await _get_collection("users")
    await users.update_many(
        {"notification_token": {"$in": tokens}},
        {"$unset": {"notification_token": ""}},
    )
    current_app.logger.info(f"Dropped {len(tokens)} dead push token(s)")


# --------------------------------------------------------------------------- #
# Sending
# --------------------------------------------------------------------------- #

def _chunk(items: List[Any], size: int) -> List[List[Any]]:
    """Split a list into fixed-size chunks."""
    return [items[index:index + size] for index in range(0, len(items), size)]


def _truncate(text: str, limit: int = MAX_BODY_LENGTH) -> str:
    """Shorten notification text so the OS banner does not clip mid-word."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _expo_headers() -> Dict[str, str]:
    """Headers for the Expo push endpoint, including the token when configured."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
    }
    if Config.EXPO_TOKEN:
        headers["Authorization"] = f"Bearer {Config.EXPO_TOKEN}"
    return headers


async def send_push_messages(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Deliver one notification to many devices.

    Returns a summary dict -- this never raises, because a failed push must
    never fail the action that triggered it.
    """
    valid_tokens = [token for token in tokens if is_valid_expo_token(token)]

    if not valid_tokens:
        current_app.logger.info("No registered push tokens; skipping send")
        return {"sent": 0, "failed": 0, "skipped": True}

    payload_body = _truncate(body)
    sent = 0
    failed = 0
    dead_tokens: List[str] = []

    for batch in _chunk(valid_tokens, EXPO_BATCH_SIZE):
        messages = [
            {
                "to": token,
                "title": title,
                "body": payload_body,
                "sound": "default",
                "priority": "high",
                "channelId": "announcements",
                "data": data or {},
            }
            for token in batch
        ]

        try:
            response = await current_app.http_client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers=_expo_headers(),
                timeout=15.0,
            )
            response.raise_for_status()
            tickets = response.json().get("data", [])
        except Exception as exc:
            current_app.logger.error(f"Expo push request failed: {exc}")
            failed += len(batch)
            continue

        # Tickets come back in the same order as the messages we sent.
        for index, ticket in enumerate(tickets):
            if ticket.get("status") == "ok":
                sent += 1
                continue

            failed += 1
            error = (ticket.get("details") or {}).get("error")
            current_app.logger.warning(
                f"Push ticket error for token {batch[index]}: {ticket.get('message')} ({error})"
            )
            if error in DEAD_TOKEN_ERRORS:
                dead_tokens.append(batch[index])

    await _drop_dead_tokens(dead_tokens)

    current_app.logger.info(f"Push '{title}': {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "skipped": False}


async def send_to_all(
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    exclude_user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Send a notification to every device with a registered token."""
    tokens = await get_device_tokens(exclude_user_id=exclude_user_id)
    return await send_push_messages(tokens, title, body, data)


async def send_to_users(
    user_ids: List[int],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Send a notification to a specific set of users."""
    tokens = await get_device_tokens_for_users(user_ids)
    return await send_push_messages(tokens, title, body, data)


# --------------------------------------------------------------------------- #
# Announcements
# --------------------------------------------------------------------------- #

async def broadcast_announcement(
    update_text: str,
    update_id: Optional[int] = None,
    created_by: Optional[int] = None,
) -> Dict[str, Any]:
    """Push a newly created announcement to the whole team.

    The author is excluded -- they just typed it, they don't need the banner.
    """
    try:
        return await send_to_all(
            title="New Announcement",
            body=update_text,
            data={"type": "announcement", "id": update_id},
            exclude_user_id=created_by,
        )
    except Exception as exc:
        current_app.logger.error(f"Failed to broadcast announcement: {exc}")
        return {"sent": 0, "failed": 0, "skipped": True, "error": str(exc)}
