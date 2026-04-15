import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from app import app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def run_flask():
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Flask API on port {port}...")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_flask()