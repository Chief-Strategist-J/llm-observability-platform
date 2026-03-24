import asyncio
import logging
import os
import jwt
import datetime
from pathlib import Path
from dotenv import load_dotenv
from agents.custom_agent import run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_videosdk_token(api_key: str, secret_key: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "apikey": api_key,
        "permissions": ["allow_join", "allow_mod"],
        "version": 2,
        "iat": int(datetime.datetime.now().timestamp()),
        "exp": int((datetime.datetime.now() + datetime.timedelta(hours=24)).timestamp()),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256", headers=header)

def main():
    load_dotenv()
    
    meeting_id = os.getenv("VIDEOSDK_MEETING_ID")
    token = os.getenv("VIDEOSDK_TOKEN")
    api_key = os.getenv("VIDEOSDK_API_KEY")
    secret_key = os.getenv("VIDEOSDK_SECRET_KEY")
    google_ai_key = os.getenv("GOOGLE_AI_KEY")
    
    if not token and api_key and secret_key:
        logger.info("Generating VideoSDK token from API key and Secret key...")
        token = generate_videosdk_token(api_key, secret_key)
    
    missing_vars = []
    if not meeting_id:
        missing_vars.append("VIDEOSDK_MEETING_ID")
    if not token:
        missing_vars.append(
            "VIDEOSDK_TOKEN or (VIDEOSDK_API_KEY and VIDEOSDK_SECRET_KEY)"
        )
    if not google_ai_key:
        missing_vars.append("GOOGLE_AI_KEY")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        logger.info("Please set them in your .env file or environment.")
        return

    meeting_url = f"https://app.videosdk.live/meetings/{meeting_id}"
    print("\n" + "="*50)
    print(f"JOIN THE MEETING HERE: {meeting_url}")
    print("="*50 + "\n")

    try:
        asyncio.run(
            run_agent(
                meeting_id=meeting_id,
                token=token,
                google_ai_key=google_ai_key
            )
        )
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
