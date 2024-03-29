# Import necessary modules from the cryptography library
import cryptography
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import os

#32-byte AES key generation
def generate_aes_key():
    return os.urandom(32)

def encrypt_aes_key(aes_key, rsa_public_key):
    # Encrypt the AES key using RSA-OAEP
    encrypted_key = rsa_public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    # Return the encrypted key
    return encrypted_key

def decrypt_aes_key(encrypted_key, rsa_private_key):
    # Decrypt the encrypted AES key using RSA-OAEP
    aes_key = rsa_private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    # Return the decrypted AES key
    return aes_key

def encrypt_file(file_path, key):
    nonce = os.urandom(12)  # GCM requires a 96-bit (12-byte) nonce
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())

    with open(file_path, 'rb') as f:
        plaintext = f.read()

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

 # Get the authentication tag generated by GCM
    tag = encryptor.tag

    # Save nonce, tag, and ciphertext
    return nonce + tag + ciphertext


def decrypt_file(ciphertext, key):
    nonce = ciphertext[:12]  # Extract the nonce
    tag = ciphertext[12:28]   # Extract the authentication tag
    ciphertext_data = ciphertext[28:]  # Extract the actual ciphertext

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Authenticate and decrypt the ciphertext
    plaintext = decryptor.update(ciphertext_data) + decryptor.finalize()

    return plaintext


def generate_rsa_key_pair():
    # Generate a new RSA private key with a specified key size (2048 bits in this case)
    private_key = rsa.generate_private_key(
        public_exponent=65537, # Commonly used public exponent for RSA
        key_size=2048, # Key size in bits
        backend=default_backend() # Use the default cryptographic backend
    )

    # Extract the corresponding public key from the private key
    public_key = private_key.public_key()
    # Return the generated private key and corresponding public key
    return private_key, public_key

def save_rsa_key_to_file(key, filename, is_private=True):
    # Open the specified file in binary write mode
    with open(filename, 'wb') as f:
        # Check if the key is private or public
        if is_private:
            # Write the private key to the file in PEM format
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        else:
            # Write the public key to the file in PEM format
            f.write(key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))


def load_rsa_key_from_file(filename, is_private=True):
    # Open the specified file in binary read mode
    with open(filename, 'rb') as f:
        # Check if the key is private or public
        if is_private:
            # Load a private key from the PEM-formatted data in the file
            return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
        else:
            # Load a public key from the PEM-formatted data in the file
            return serialization.load_pem_public_key(f.read(), backend=default_backend())


def sign_data(data, private_key):
    # Generate a digital signature for the data using the private key
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    # Return the generated digital signature
    return signature


def verify_signature(data, signature, public_key):
    try:
        # Verify the digital signature using the public key
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # If verification is successful, return True
        return True
    except cryptography.exceptions.InvalidSignature:
        # If verification fails, catch the InvalidSignature exception and return False
        return False


# Example usage
    
# Two sets of RSA key pairs are generated for two users (User 1 and User 2).
user1_private_key, user1_public_key = generate_rsa_key_pair()
user2_private_key, user2_public_key = generate_rsa_key_pair()

# The private and public RSA keys for both users are saved to separate files in PEM format.
save_rsa_key_to_file(user1_private_key, 'user1_private.pem', is_private=True)
save_rsa_key_to_file(user1_public_key, 'user1_public.pem', is_private=False)
save_rsa_key_to_file(user2_private_key, 'user2_private.pem', is_private=True)
save_rsa_key_to_file(user2_public_key, 'user2_public.pem', is_private=False)

# Two AES keys are generated for two users.
user1_aes_key = generate_aes_key()
user2_aes_key = generate_aes_key()

# The generated AES keys are encrypted using the respective RSA public keys.
encrypted_user1_aes_key = encrypt_aes_key(user1_aes_key, user1_public_key)
encrypted_user2_aes_key = encrypt_aes_key(user2_aes_key, user2_public_key)

# The encrypted AES keys are saved to separate files.
with open('encrypted_user1_aes_key.pem', 'wb') as f:
    f.write(encrypted_user1_aes_key)

with open('encrypted_user2_aes_key.pem', 'wb') as f:
    f.write(encrypted_user2_aes_key)

# The encrypted AES keys are decrypted using the respective RSA private keys.
decrypted_user1_aes_key = decrypt_aes_key(encrypted_user1_aes_key, user1_private_key)
decrypted_user2_aes_key = decrypt_aes_key(encrypted_user2_aes_key, user2_private_key)

# Plaintext data is read from a file named 'example.txt'.
plaintext_file_path = 'example.txt'
with open(plaintext_file_path, 'rb') as f:
    plaintext_data = f.read()

# Print plaintext before encryption
with open(plaintext_file_path, 'rb') as f:
    plaintext_data = f.read()

print("Plaintext before encryption:", plaintext_data.decode())

# Sign the data before encryption
signature = sign_data(plaintext_data, user1_private_key)

# Include the signature along with the ciphertext
ciphertext_user1 = encrypt_file(plaintext_file_path, decrypted_user1_aes_key) + signature

# Verify the signature after decryption
received_ciphertext = ciphertext_user1[:-256]
received_signature = ciphertext_user1[-256:]

print("Received Ciphertext:", received_ciphertext)
print("Received Signature:", received_signature)

# Extract plaintext data
plaintext_data = decrypt_file(received_ciphertext, decrypted_user1_aes_key)

try:
    if verify_signature(plaintext_data, received_signature, user1_public_key):
        print("Signature is valid.")
        decrypted_text_user1 = decrypt_file(received_ciphertext, decrypted_user1_aes_key)
        print(f'Decrypted text for user 1: {decrypted_text_user1.decode()}')
    else:
        print("Signature is not valid.")
except InvalidSignature:
    print("Error: Invalid Signature.")