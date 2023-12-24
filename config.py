from dotenv import load_dotenv
load_dotenv()
import os

models = ['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4','gpt-4-32k']

class Config():
    # BEARER_TOKEN = 'Bearer SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
    BEARER_TOKEN = os.getenv('BEARER_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
    SENDER_ID = os.getenv('SENDER_ID')
    INSTAGRAM_ID = os.getenv('INSTAGRAM_ID')
    PAGE_ID = os.getenv('PAGE_ID')
    USER_ID = os.getenv('USER_ID')
    CONVERSATION_ID = os.getenv('CONVERSATION_ID')
    USER_ACCESS_TOKEN = os.getenv('USER_ACCESS_TOKEN')
    PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
    HARDCODED_INDEX_KEY = 'f010c8ba-863a-11ee-a279-20c19bff2da4'
    # HARDCODED_INDEX_KEY = 'db9555b3-7cd6-11ee-ac8f-20c19bff2da4'
    APP_ID = os.getenv('APP_ID')
    APP_SECRET = os.getenv('APP_SECRET')
    MODEL = models[0]

    
class DevelopmentConfig(Config):
    DEBUG = True
