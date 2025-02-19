from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file. You need to make this and add the key to it like this: ROBOTEVENTS_API_KEY=Bearer your_token_here

ROBOTEVENTS_API_KEY = os.getenv('ROBOTEVENTS_API_KEY')