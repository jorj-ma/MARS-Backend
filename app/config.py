import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    # This key is used to sign the tokens generated in auth.py
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'change-this-to-a-secure-key'
    
    # Optional: Set how long tokens remain valid
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)