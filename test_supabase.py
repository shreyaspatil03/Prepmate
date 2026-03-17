# test_supabase.py
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Try inserting a test row
result = supabase.table("sessions").insert({
    "sid": "test-123",
    "profile": {"name": "Test User"}
}).execute()

print("Connected successfully!")
print("Row inserted:", result.data)

# Clean up test row
supabase.table("sessions").delete().eq("sid", "test-123").execute()
print("Test row deleted. Connection is working perfectly.")


