import os
import logging
import json
import signal
import sys
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from string_processor import process_string
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

load_dotenv()

# === Preparation and Notes ===

## Prerequisites

# - **Python 3.8+** installed on your system.
# - **MongoDB** installed and running locally or accessible via a connection string.
# - **RSA Keys**: You need `private.pem` and `public.pem` files for encryption/decryption.
#   - If you don't have them, see the "Generating RSA Keys" section above.

## Installing Dependencies

# Open your terminal in the project directory and run:

# ```sh
# pip install fastapi uvicorn pymongo cryptography python-dotenv
# ```

# === FastAPI App Setup ===
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code} for {request.method} {request.url}")
    return response

# === Global Variables ===
history_file = "history.enc"
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
os_public_key_file = r"C:\Users\codel\Downloads\public.pem"
os_private_key_file = r"C:\Users\codel\Downloads\private.pem"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# === MongoDB Connection and Handling ===
def connect_to_mongo():
    retries = 5
    while retries > 0:
        try:
            mongo_client = MongoClient(mongo_uri)
            db = mongo_client["conversion_app"]
            history_collection = db["history"]
            mongo_client.server_info()
            logging.info("MongoDB connected successfully.")
            return history_collection
        except ServerSelectionTimeoutError as e:
            retries -= 1
            logging.error(f"MongoDB connection failed. Retries left: {retries}. Error: {e}")
            if retries == 0:
                raise
            time.sleep(2)

history_collection = connect_to_mongo()

# === RSA Key Management ===
def generate_os_rsa_keys():
    if not os.path.exists(os_private_key_file) or not os.path.exists(os_public_key_file):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        with open(os_private_key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(os_public_key_file, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        logging.info("RSA keys generated and saved (no password protection).")

def load_os_rsa_keys():
    try:
        with open(os_private_key_file, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(os_public_key_file, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        logging.info("RSA keys loaded successfully.")
        return private_key, public_key
    except Exception as e:
        logging.error(f"Error loading RSA keys: {e}")
        raise

# === Encryption and Decryption ===
def encrypt_data(data: str, public_key) -> bytes:
    try:
        return public_key.encrypt(
            data.encode(),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(), label=None)
        )
    except Exception as e:
        logging.error(f"Error encrypting data: {e}")
        raise

def decrypt_data(encrypted_data: bytes, private_key) -> str:
    try:
        return private_key.decrypt(
            encrypted_data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(), label=None)
        ).decode()
    except Exception as e:
        logging.error(f"Error decrypting data: {e}")
        raise

def save_history(history, public_key):
    try:
        encrypted_data = encrypt_data(json.dumps(history), public_key)
        with open(history_file, "wb") as f:
            f.write(encrypted_data)
        logging.info("Encrypted history saved to local file.")
    except Exception as e:
        logging.error(f"Error saving encrypted history: {e}")
        raise

def load_history(private_key):
    try:
        if not os.path.exists(history_file):
            logging.info("No encrypted history file exists.")
            return []
        with open(history_file, "rb") as f:
            encrypted_data = f.read()
        if not encrypted_data:
            return []
        return json.loads(decrypt_data(encrypted_data, private_key))
    except Exception as e:
        logging.error(f"Error loading encrypted history: {e}")
        return []

# === Initialize RSA Keys ===
generate_os_rsa_keys()
os_private_key, os_public_key = load_os_rsa_keys()

# === Request Models ===
class ConvertRequest(BaseModel):
    input_string: str

# === API Endpoints ===
@app.api_route("/api/convert", methods=["GET", "POST"])
async def convert(request: Request, input_string: str = None):
    if request.method == "POST":
        body = await request.json()
        input_string = body.get("input_string", "").strip()
    elif request.method == "GET" and input_string:
        input_string = input_string.strip()

    logging.info(f"Converting input string: {input_string}")

    if not input_string:
        raise HTTPException(status_code=400, detail="Input string is required")
    if len(input_string) > 1000:
        raise HTTPException(status_code=400, detail="Input string is too long")
    if not input_string.isascii():
        raise HTTPException(status_code=400, detail="Input string contains invalid characters")

    try:
        result = process_string(input_string)
        # Save conversion history to MongoDB
        history_collection.insert_one({"input": input_string, "output": result})
        logging.info(f"Saved to MongoDB: {input_string} -> {result}")
        return {"input": input_string, "result": result}
    except Exception as e:
        logging.error(f"Error processing input: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/history")
def get_history():
    try:
        # Retrieve history from MongoDB
        history = list(history_collection.find({}, {"_id": 0}))
        return {"history": history}
    except Exception as e:
        logging.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# === Startup Hook ===
@app.on_event("startup")
def startup_event():
    try:
        # Try to detect if the data is encrypted (has 'encrypted' field)
        encrypted_docs = list(history_collection.find({"encrypted": {"$exists": True}}, {"_id": 0, "encrypted": 1}))
        if encrypted_docs:
            # Decrypt all and replace with decrypted docs
            decrypted_history = []
            for doc in encrypted_docs:
                decrypted_json = decrypt_data(doc["encrypted"], os_private_key)
                decrypted_history.append(json.loads(decrypted_json))
            history_collection.delete_many({})
            if decrypted_history:
                history_collection.insert_many(decrypted_history)
            logging.info("MongoDB decrypted on startup.")
        else:
            logging.info("MongoDB already contains decrypted data on startup.")
    except Exception as e:
        logging.warning(f"Failed to decrypt MongoDB data on startup: {e}")

# === Shutdown Hook ===
@app.on_event("shutdown")
def encrypt_before_shutdown():
    try:
        # Get all history in decrypted form
        history = list(history_collection.find({}, {"_id": 0}))
        # Encrypt each entry and overwrite the collection
        encrypted_history = []
        for entry in history:
            encrypted_entry = encrypt_data(json.dumps(entry), os_public_key)
            # Store as binary in MongoDB
            encrypted_history.append({"encrypted": encrypted_entry})
        # Replace all documents with encrypted ones
        history_collection.delete_many({})
        if encrypted_history:
            history_collection.insert_many(encrypted_history)
        logging.info("MongoDB overwritten with encrypted data on shutdown.")
    except Exception as e:
        logging.error(f"Error encrypting MongoDB data on shutdown: {e}")

# === Signal Handling ===
def handle_shutdown(signal_num, frame):
    logging.info("Shutting down server...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# === Run FastAPI App ===
if __name__ == "__main__":
    logging.info("Starting FastAPI server on http://localhost:8000")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    logging.info("FastAPI server stopped.")