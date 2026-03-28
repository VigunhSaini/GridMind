import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv("DATABASE_URL")

print(f"DATABASE_URL: {db_url[:30]}... (truncated)")

if not db_url or "YOUR_PROJECT_REF" in db_url:
    print("❌ DATABASE_URL is not set properly.")
else:
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ DB Connection Successful. Result: {result.fetchone()[0]}")
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")
