import base64
import os # added this import
from src.robinhood_api.api_client import APIClient
from src.robinhood_api.orders import Orders
from src.robinhood_api.market_data import MarketData
from src.robinhood_api.account import Account

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the keys directory
keys_dir = os.path.join(current_dir, "keys")

# Construct the absolute path to private_key_base64.txt
private_key_path = os.path.join(keys_dir, "private_key_base64.txt")

# Construct the absolute path to RH_key.txt
rh_key_path = os.path.join(keys_dir, "RH_key.txt")

# Read the private key
with open(private_key_path, 'r') as private_file:
    BASE64_PRIVATE_KEY = private_file.read().strip()

# Read the private key
with open(rh_key_path, 'r') as rh_key:
    API_KEY = rh_key.read().strip()

class CryptoAPITrading:
    """
    Main class for interacting with the Robinhood API.
    """
    def __init__(self):
        private_bytes = base64.b64decode(BASE64_PRIVATE_KEY)
        self.api_client = APIClient(API_KEY, private_bytes)
        self.orders = Orders(self.api_client)
        self.market_data = MarketData(self.api_client)
        self.account = Account(self.api_client)