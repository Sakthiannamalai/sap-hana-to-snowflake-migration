import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

def get_env_variable(key: str, default_value: str = None) -> str:
    """
    Fetch an environment variable's value.
    :param key: The environment variable's key
    :param default_value: Default value to return if the variable is not found
    :return: Value of the environment variable or the default value
    """
    return os.getenv(key, default_value)

APP_NAME = get_env_variable("APP_NAME", "My FastAPI Application")
VERSION = get_env_variable("VERSION", "0.1.0")
API_KEY = get_env_variable("API_KEY")
AWS_ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_env_variable("AWS_SECRET_ACCESS_KEY")
S3_REGION = get_env_variable("S3_REGION", "")
S3_BUCKET_PATH= get_env_variable("S3_BUCKET_PATH", "")
S3_BUCKET_NAME = get_env_variable("S3_BUCKET_NAME")
PRESIGNED_URL_EXPIRY = get_env_variable("PRESIGNED_URL_EXPIRY")
WEBAPP_USERNAME = get_env_variable("WEBAPP_USERNAME")
WEBAPP_PASSWORD = get_env_variable("WEBAPP_PASSWORD")
WEBAPP_REMEMBERME = get_env_variable("WEBAPP_REMEMBER")
WEBAPP_AUTH_URL = get_env_variable("WEBAPP_AUTH_URL")
WEBAPP_URL = get_env_variable("WEBAPP_URL")
