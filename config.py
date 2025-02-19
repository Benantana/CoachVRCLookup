from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

ROBOTEVENTS_API_KEY = os.getenv('ROBOTEVENTS_API_KEY')