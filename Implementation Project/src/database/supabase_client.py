from supabase import create_client 
import os # access environment variables (ex. supabase_url)
from dotenv import load_dotenv # allows .env for os to read
from pathlib import Path # efficiently builds path

import httpx # for handling connection errors

dotenv_path = Path(__file__).resolve().parent.parent/"CNN"/".env"



print("Looking for .env at:", dotenv_path)
print("Exists?", dotenv_path.exists())

load_dotenv(dotenv_path)


# initializes the subpabase client using the creds from .env
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

def insert_detection(species: str, confidence: float):
    try:
        supabase.table("Detections").insert({
            "species": species,
            "confidence": round(confidence, 4)
        }).execute()

    except httpx.ConnectError:
        print("Database connection lost — skipping insert")

    except Exception as e:
        print("Database error:", e)
