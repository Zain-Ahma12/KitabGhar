import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()

API_KEY = os.getenv("X-API-KEY")

def verify_api_key(api_key: str = Header()) -> API_KEY:
    """
    Verify that the provided API key matches the expected value.
    an HTTPException if the keys do not match.
    """
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key