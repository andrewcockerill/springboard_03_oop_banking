from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv, dotenv_values
import os
import logging
from app_utils import CredentialHandler

# Constants
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DB_NAME = "banking"
INIT_CONNECT_STR = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{HOST}:{PORT}"
DB_CONNECT_STR = INIT_CONNECT_STR+f"/{DB_NAME}"

# Connections
engine = create_engine(DB_CONNECT_STR)
session = sessionmaker(bind=engine)()

# Logging
logger = logging.getLogger('application_main')
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('../logs/banking_app_logs.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

# App main loop
if __name__ == '__main__':
    logger.info('banking application started')
    try:
        ch = CredentialHandler(session, logger)
        ch.start_screen()
    except Exception as e:
        logger.error(e)
        logger.error('banking application ended unexpectedly')
    finally:
        logger.info('banking application ended successfully')
        session.close()
        engine.dispose()
        print('Goodbye!')
