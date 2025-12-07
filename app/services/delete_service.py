from app.telegram_client.client import telethon_client, ensure_client_started

async def delete_file(chat_id: int, message_id: int, revoke: bool = False) -> dict:
    """
    Deletes a message from a Telegram chat.
    The 'revoke' parameter determines if the message should be deleted for everyone (True)
    or just for the client (False).
    """
    try:
        await ensure_client_started()
        # telethon_client.delete_messages returns a list of Message objects that were deleted
        deleted_messages = await telethon_client.delete_messages(chat_id, message_id, revoke=revoke)

        if deleted_messages:
            return {"status": "success", "message": f"Message {message_id} deleted from chat {chat_id}"}
        else:
            # This might happen if the message doesn't exist or the client doesn't have permission
            return {"status": "fail", "message": f"Failed to delete message {message_id} from chat {chat_id}. It might not exist or permissions are insufficient."}
    except Exception as e:
        return {"status": "fail", "message": f"An error occurred while deleting message {message_id}: {str(e)}"}
