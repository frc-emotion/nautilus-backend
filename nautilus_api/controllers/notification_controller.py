import datetime
from typing import Any, Dict
from exponent_server_sdk_async import (
    AsyncPushClient,
    PushMessage,
    DeviceNotRegisteredError,
    PushTicketError,
    PushServerError
)
from quart import current_app
from nautilus_api.config import Config
from nautilus_api.controllers.utils import error_response, success_response, validate_data
from nautilus_api.schemas.notification_schema import TriggerNotificationSchema
from nautilus_api.services import notification_service

async def update_notification_token(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a user's notification token by user ID."""

    if "token" not in data:
        return error_response("Token not provided", 400)

    if not (result := await notification_service.update_notification_token(user_id, data.get("token"))).modified_count:
        return error_response("Not found or unchanged", 404)
    
    return success_response("Notification token updated", 200)

async def delete_notification_token(user_id: int) -> Dict[str, Any]:
    """Delete a user's notification token by user ID."""
    if not (result := await notification_service.delete_notification_token(user_id)).modified_count:
        return error_response("Not found or unchanged", 404)

    return success_response("Notification token deleted", 200)

async def trigger_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger a notification for a user."""
    validated_data, error = validate_data(data, TriggerNotificationSchema)

    if error:
        return validated_data

    if not (user := await notification_service.find_user_by_id(data["user_id"])):
        return error_response("User not found", 404)
    
    token = user.get("notification_token")

    # Send notification to user
    current_app.logger.info(f"Sending notification to user {user['user_id']} with message: {data['message']}")

    try:
        response = await current_app.push_client.publish(PushMessage(
                to=token,
                body=validated_data.message,
                badge=1,
                title=validated_data.title,
                sound="default"
            ))
        current_app.logger.info(f"Sent notifications: {response}")
        return success_response(f"Notification sent: {str(exc)}", 200)
    except PushServerError as exc:
        current_app.logger.error(f"PushServerError: {exc}")
        return error_response(f"Failed to send notifications: {str(exc)}", 500)
    except PushTicketError as exc:
        current_app.logger.error(f"PushTicketError: {exc}")
        return error_response(f"Failed to send notifications: {str(exc)}", 500)
    except Exception as exc:
        current_app.logger.error(f"Unexpected error: {exc}")
        return error_response(f"Failed to send notifications: {str(exc)}", 500)

async def trigger_mass_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger a notification for all users."""
    validated_data, error = validate_data(data, TriggerNotificationSchema)

    if error:
        return validated_data

    users = await notification_service.get_all_notification_tokens()

    tokens = []

    for user in users:
        tokens.append(
            PushMessage(
                to=user["notification_token"],
                body=validated_data.message,
                badge=1,
                title=validated_data.title,
                sound="default"
            )
        )

    success = []
    failed = []

    try:
        push_tickets = await current_app.push_client.publish_multiple(tokens)
        for push_ticket in push_tickets:
            if push_ticket.is_success():
                success.append(push_ticket)
            else:
                failed.append(push_ticket)
        
        return success_response(f"Notification sent to {len(success)} users, failed to send to {len(failed)}", 200, {"success": success, "failed": failed})
    except DeviceNotRegisteredError as exc:
        current_app.logger.error(f"Failed to send notifications: {str(exc)}")
        return error_response(f"Failed to send notifications: {str(exc)}", 400)
    except PushServerError as exc:
        current_app.logger.error(f"Failed to send notifications: {str(exc)}")
        return error_response(f"Failed to send notifications: {str(exc)}", 500)
    except PushTicketError as exc:
        return error_response(f"Failed to send notifications: {str(exc)}", 500)
    except Exception as exc:
        return error_response(f"Failed to send notifications: {str(exc)}", 500)
    
async def check_notification_token(user_id: int) -> Dict[str, Any]:
    """Check if user has a notification token."""
    if not (user := await notification_service.find_user_by_id(user_id)):
        return error_response("User not found", 404)

    if not user.get("notification_token"):
        return error_response("No notification token set", 404)

    return success_response("Notification token found", 200, {"token": user.get("notification_token")})

def get_submission_time():
    now = datetime.datetime.now()
    date_string = now.strftime("%a, %b %d, %Y")
    time_string = now.strftime("%I:%M:%S %p")
    submission_time = f"Submitted on {date_string} at {time_string}"
    return submission_time

async def send_contact_form(data):
    validated_data=data
    submission_time = get_submission_time()

    data = {i:data[i].replace("@everyone",'@ everyone').replace("@here",'@ here') for i in data}

    subject = data["subject"]
    fieldsArr = [
            {
                "name": "Name",
                "value": data["name"],
            },
            {
                "name": "Email",
                "value": data["email"],
            },
            {
                "name": "Message",
                "value": data["message"],
            },
        ]
    if data["company"]:
        fieldsArr.insert(1, {
            "name" : "Company",
            "value": data["company"]
            })

    response = await current_app.http_client.post(
        Config.DISCORD_WEBHOOK,
        json={
            "username": "team2658.org",
            "avatar_url":
                "https://avatars.githubusercontent.com/u/36017746?s=400&u=e55b83cf74c03119a931a08fb43d566f9087cfa0&v=4",
            "content": "New form submission🚨🚨🚨🚨🚨🚨🚨",
            "embeds": [
                {
                    "title": "Subject: " + subject,
                    "description":submission_time,
                    "color": 15985179,
                    "fields": fieldsArr
                }
            ]
        },
        headers={
        "Content-Type": "application/json"
    }
    )

    return response

    