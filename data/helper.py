"The bot helper"
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

class bot:
    prefix = os.getenv('BOT_PREFIX')

    

def getenv(key: str):
    """Get an environment variable"""
    return os.getenv(key)

class system:
    started_at = datetime.datetime.now()
    logfile_format = '%d%m%Y-%H-%M'