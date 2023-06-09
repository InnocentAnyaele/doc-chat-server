from dotenv import load_dotenv
load_dotenv()
import os

class Config():
    # BEARER_TOKEN = 'Bearer SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
    BEARER_TOKEN = os.getenv('BEARER_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    SENDER_ID = os.getenv('SENDER_ID')
    PAGE_ID = os.getenv('PAGE_ID')
    USER_ID = os.getenv('USER_ID')
    CONVERSATION_ID = os.getenv('CONVERSATION_ID')
    USER_ACCESS_TOKEN = os.getenv('USER_ACCESS_TOKEN')
    PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
    HARDCODED_INDEX_KEY = 'bb02481f-eb66-11ed-9c16-20c19bff2da0'
    APP_ID = os.getenv('APP_ID')
    APP_SECRET = os.getenv('APP_SECRET')

    
class DevelopmentConfig(Config):
    DEBUG = True
