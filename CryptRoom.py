def encrypt(text):
    return ''.join(chr(ord(c) + 1) for c in text)

def decrypt(text):
    return ''.join(chr(ord(c) - 1) for c in text)

print("CryptRoom ready.")
