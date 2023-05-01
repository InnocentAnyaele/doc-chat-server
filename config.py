from dotenv import load_dotenv
load_dotenv()
import os

class Config():
    BEARER_TOKEN = 'Bearer SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

class DevelopmentConfig(Config):
    DEBUG = True
