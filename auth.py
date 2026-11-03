import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()

API_KEY = os.getenv("X-API-KEY")


def verify_api_key(x_api_key: str = Header()) -> str:
    """
    Verify that the "x-api-key" header matches the expected value.
    Raises an HTTPException (401) if the keys do not match.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return x_api_key