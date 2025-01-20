import json
import redis

from app.config import redis_client
from app.utils import logger


def update_status(unique_id, status, percentage):
    """
    Update the status data in Redis for a given unique ID.

    Args:
        unique_id (str): The unique identifier for the status.
        status (str): The current status (e.g., 'In Progress', 'Completed').
        percentage (int): The completion percentage (e.g., 50 for 50%).
    """
    try:
        status_data = {
            "status": status,
            "percentage": percentage
        }

        redis_client.set(unique_id, json.dumps(status_data))
        logger.info(f"Updated status for unique_id {unique_id}: {status_data}")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred while updating status for unique_id {
                     unique_id}: {e}")
        raise
