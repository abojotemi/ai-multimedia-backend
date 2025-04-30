import os
import motor
import beanie
from src.models.activity_log import ActivityLog
from src.models.folder import Folder
from src.models.media_item import MediaItem
from src.models.stats_and_analytics import Stats, Analytics
from src.models.user import User
from src.models.token import BlacklistedToken
from src.models.user_stats import UserStats


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
async def init_mongodb(db_name: str):
    conn_str = f"{MONGODB_URL}/{db_name}"
    client = motor.motor_asyncio.AsyncIOMotorClient(conn_str)
    await beanie.init_beanie(
        database=client[db_name], 
        document_models=[
            Stats, 
            Analytics, 
            User, 
            MediaItem, 
            ActivityLog, 
            Folder, 
            BlacklistedToken,
            UserStats
        ]
    )
    print(f"Connected to {db_name}.")
