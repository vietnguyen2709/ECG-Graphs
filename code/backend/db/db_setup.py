from dotenv import load_dotenv
import os
import pymysql
load_dotenv()

# Database setup
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'ssl': {
        'ssl-ca': os.path.abspath('certs/DigiCertGlobalRootG2.crt.pem'),
        'ssl-mode': 'VERIFY_IDENTITY'  # Ensures proper verification
    },
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)
