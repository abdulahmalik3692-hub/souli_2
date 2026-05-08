import os
import certifi
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGODB_URI = os.environ.get('MONGODB_URI', '')
DB_NAME     = os.environ.get('DB_NAME', 'soulify_db')

client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
)

db = client[DB_NAME]

mood_logs   = db['mood_logs']
user_quotes = db['user_quotes']
users       = db['users']


async def save_mood_log(user_id: str, emotion: str,
                        confidence: float, message: str):
    import datetime
    try:
        await mood_logs.insert_one({
            'user_id':         user_id,
            'emotion':         emotion,
            'confidence':      confidence,
            'message_preview': message[:80],
            'timestamp':       datetime.datetime.utcnow()
        })
    except Exception:
        pass


async def get_mood_history(user_id: str, days: int = 7) -> list:
    import datetime
    try:
        since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        cursor = mood_logs.find(
            {'user_id': user_id, 'timestamp': {'$gte': since}},
            {'_id': 0, 'emotion': 1, 'confidence': 1, 'timestamp': 1}
        ).sort('timestamp', -1)
        return await cursor.to_list(length=100)
    except Exception:
        return []
