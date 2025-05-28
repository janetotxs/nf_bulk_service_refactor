from dotenv import load_dotenv
import os

# Load the .env file only once when the module is imported
load_dotenv()

def get_env_variable(key: str) -> str:
    value = os.getenv(key)

    if not value:
        raise ValueError(f"Environment variable '{key}' is not set!")
    
    return value