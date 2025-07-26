import socket
import threading
import os
import binascii
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# ===============================
# 🔐 Encryption & Decryption
# ===============================
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_message(message: str, password: str) -> str:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    return salt.hex() + encrypted.decode()

def decrypt_combined(combined: str, password: str) -> str:
    salt_hex = combined[:32]
    encrypted = combined[32:]
    salt = binascii.unhexlify(salt_hex)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    return fernet.decrypt(encrypted.encode()).decode()

# ===============================
# 💬 Chat Handler
# ===============================
def receive_messages(conn, password):
    while True:
        try:
            data = conn.recv(4096)
            if data:
                msg = decrypt_combined(data.decode(), password)
                print(f"\n📩 Friend: {msg}\n🧑‍💻 You: ", end="")
        except Exception as e:
            print("\n❌ Error receiving message:", e)
            break

def send_messages(conn, password):
    while True:
        msg = input("🧑‍💻 You: ")
        if msg.lower() == "exit":
            conn.close()
            break
        encrypted = encrypt_message(msg, password)
        try:
            conn.sendall(encrypted.encode())
        except Exception as e:
            print("❌ Error sending:", e)

# ===============================
# 🚀 Main Function
# ===============================
def start_chat(is_host, host, port, password):
    if is_host:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((host, port))
            server.listen(1)
            print(f"🔌 Waiting for connection on {host}:{port} ...")
            conn, addr = server.accept()
            print(f"✅ Connected with {addr[0]}")

            threading.Thread(target=receive_messages, args=(conn, password), daemon=True).start()
            send_messages(conn, password)
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            try:
                conn.connect((host, port))
                print(f"✅ Connected to {host}:{port}")
                threading.Thread(target=receive_messages, args=(conn, password), daemon=True).start()
                send_messages(conn, password)
            except Exception as e:
                print("❌ Connection failed:", e)

# ===============================
# 🏁 Start Point
# ===============================
if __name__ == "__main__":
    print("\n🔐 Secure Two-Way Chat Room")
    role = input("Are you host or join? [host/join]: ").strip().lower()
    port = 65432
    password = input("🔑 Enter room password: ")

    if role == "host":
        host = "0.0.0.0"  # Listen on all network interfaces
        start_chat(is_host=True, host=host, port=port, password=password)
    elif role == "join":
        host = input("Enter host IP to connect: ").strip()
        start_chat(is_host=False, host=host, port=port, password=password)
    else:
        print("❌ Invalid choice. Please enter 'host' or 'join'.")
