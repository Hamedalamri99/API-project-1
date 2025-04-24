# 🔐 API Project: Encrypted History String Processor

## 📌 Overview

This project is a **FastAPI-based web service** that processes input strings into integer lists using custom decoding rules. Its key innovation lies in **secure and ephemeral data visibility**: all input-output history is **stored encrypted in MongoDB when the server is offline** and **decrypted at runtime**—making history accessible only during server execution.

---

## 🚀 Features

- **`POST /api/convert`** — Processes an input string and returns the computed list of integers.
- **`GET /api/history`** — Retrieves all historical conversion records (only while the server is running).
- **AES-encrypted history at rest** (stored encrypted in MongoDB when the server is shut down).
- **Automatic decryption on startup** using RSA private key.
- **Secure design**: MongoDB only contains readable data while the server is live.

---

## ⚙️ How It Works

### 🔓 1. Startup

- Loads RSA keys (`private.pem`, `public.pem`).
- Decrypts encrypted entries from MongoDB using the private key.
- Makes decrypted history available for API access.

### 🧠 2. Processing Logic

When a POST request is made to `/api/convert`, the server:
- Assigns values to characters:  
  `a=1`, ..., `z=26`; `_` and `-` have `0` value.
- `z` initiates a group that includes itself and all subsequent characters.
- Groups are evaluated, and their character values are summed.
- Result is stored in MongoDB in readable form.

### 🗂 3. History Access

- The `/api/history` endpoint returns all previously processed input-output pairs in JSON format.
- Only available while the server is running.

### 🔐 4. Shutdown

- Reads all plaintext entries.
- Encrypts each using the RSA public key.
- Overwrites MongoDB documents with their encrypted versions.
- Removes decrypted documents to ensure history is safe at rest.

---

## 🔁 Workflow Summary

| Stage         | MongoDB Contents        |
|---------------|--------------------------|
| Startup       | 🔐 Encrypted → 🔓 Decrypted |
| Runtime       | 📖 Plaintext (readable)  |
| Shutdown      | 🔐 Plaintext → Encrypted  |

---

## 🛡️ Security Benefits

- Encrypted-at-rest architecture protects against data exposure when the server is offline.
- Data can only be decrypted using the **private key**, keeping sensitive records confidential.
- MongoDB contains no readable records after shutdown.

---

## 🧪 Example Usage

### ✅ Convert String

**Endpoint**: `POST /api/convert`  
**Request Body**:
```json
{
  "input_string": "dz_a_aazzaaa"
}
```

**Sample Output**:
```json
{
  "output": [28, 53, 1]
}
```

---

## 🔍 Example MongoDB Document (During Runtime)

```json
{
  "input": "dz_a_aazzaaa",
  "output": [28, 53, 1]
}
```

---

## 🔐 Generating RSA Keys

If you don’t already have keys, generate them using OpenSSL:

```sh
# Generate a 2048-bit private RSA key
openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048

# Generate the public key from the private key
openssl rsa -pubout -in private.pem -out public.pem
```

---

## ⚙️ Setup & Installation

### ✅ Prerequisites

- **Python 3.8+**
- **MongoDB** (local or remote instance)
- RSA key pair: `private.pem` and `public.pem`

### 📦 Install Dependencies

Run this in your project directory:

```sh
pip install fastapi uvicorn pymongo cryptography python-dotenv
```

### 🔗 MongoDB Configuration

The app connects to MongoDB using:

```python
os.getenv("MONGODB_URI", "mongodb://localhost:27017")
```

To override, define the `MONGODB_URI` variable in a `.env` file or system environment.

---

## 🛠️ Troubleshooting

- **MongoDB connection issues**:  
  Ensure the database server is running and reachable.

- **Key file errors**:  
  Verify both `private.pem` and `public.pem` exist and are accessible.

- **History not decrypted on startup**:  
  Confirm that the public/private key pair used matches those used during encryption.

---

## 📁 Project Structure (Simplified)

```
.
├── app.py                  # FastAPI application
├── encryption.py           # RSA encryption/decryption helpers
├── logic.py                # String processing logic
├── database.py             # MongoDB utilities
├── public.pem              # RSA public key (used at shutdown)
├── private.pem             # RSA private key (used at startup)
└── README.md               # Project documentation
```

---

## 📬 License

MIT License. You are free to use, modify, and distribute this project.

---

## 🤝 Contributing

Feel free to open issues or submit pull requests to enhance functionality or improve security.

---

## 🌐 Web Frontend

This project includes a simple, modern web interface for interacting with the API:

### `index.html`

- The main HTML file for the web interface.
- Uses [Bootstrap 5](https://getbootstrap.com/) for a clean, responsive design.
- Lets users:
  - Enter a string and submit it for processing.
  - Instantly see the output result.
  - View the full history of processed strings and their results.
  - Clear the displayed results and history.
- Displays a friendly icon and clear instructions for ease of use.

### `app.js`

- Handles all frontend logic and API communication.
- Sends user input to the backend (`/api/convert`) and displays the output.
- Fetches and displays the full history from the backend (`/api/history`).
- Updates the UI dynamically without reloading the page.
- Ensures the output and history are always up-to-date after each conversion.

**How to use:**  
Just open `index.html` in your browser while the FastAPI server is running.  
All processing and history management will work automatically!
