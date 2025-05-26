import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'sistema_nutricionista')
}

APP_CONFIG = {
    'name': os.getenv('APP_NAME', 'Sistema de Nutricionista'),
    'version': os.getenv('APP_VERSION', '1.0'),
    'window_size': (1400, 900)
}