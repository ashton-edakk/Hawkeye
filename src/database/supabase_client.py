from supabase import create_client 
import os # access environment variables (ex. supabase_url)
from dotenv import load_dotenv # allows .env for os to read
from pathlib import Path # efficiently builds path

dotenv_path = Path(__file__).resolve().parent.parent/"CNN"/".env" # builds path to .env in CNN folder
load_dotenv(dotenv_path)

# initializes the subpabase client using the creds from .env
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

def insert_detection(species: str, confidence: float):
    """Insert a detected animal species and confidence score into the Supabase database."""
    supabase.table("Detections").insert({
        "species": species,
        "confidence": round(confidence, 4)
    }).execute()