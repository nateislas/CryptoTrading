import ed25519
import base64

# Generate an Ed25519 keypair
secret_key, public_key = ed25519.create_keypair()

# Convert keys to base64 strings
private_key_base64 = base64.b64encode(secret_key.to_bytes()).decode()
public_key_base64 = base64.b64encode(public_key.to_bytes()).decode()

# Save the keys to files
with open('private_key_base64.txt', 'w') as private_file:
    private_file.write(private_key_base64)

with open('public_key_base64.txt', 'w') as public_file:
    public_file.write(public_key_base64)

print("Keys have been saved to private_key_base64.txt and public_key_base64.txt")