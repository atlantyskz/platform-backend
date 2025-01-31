import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import json
import requests

def get_public_key(test_mode=True):
    """Get the public RSA key from the server"""
    url = "https://testepay.homebank.kz/api/public.rsa"
    response = requests.get(url)
    return RSA.importKey(response.content)

def create_cryptogram(card_number, exp_date, cvc, terminal_id, test_mode=True):
    """
    Create an encrypted cryptogram for payment
    
    Args:
        card_number (str): Card number without spaces
        exp_date (str): Expiration date in MMYY format
        cvc (str): Card verification code
        terminal_id (str): Terminal ID from credentials
        test_mode (bool): Whether to use test environment
    
    Returns:
        str: Base64 encoded encrypted cryptogram
    """
    # Create the cryptogram data structure
    crypto_data = {
        "hpan":"4405639704015096",
        "expDate":"0127",
        "cvc":"321",
        "terminalId":"67e34d63-102f-4bd1-898e-370781d0074d"
    }
    
    # Convert to JSON string
    json_data = json.dumps(crypto_data, separators=(',', ':'))
    
    # Get public key
    public_key = get_public_key(test_mode)
    
    # Create cipher
    cipher = PKCS1_v1_5.new(public_key)
    
    # Encrypt the data
    encrypted_data = cipher.encrypt(json_data.encode('utf-8'))
    
    # Convert to base64
    return base64.b64encode(encrypted_data).decode('utf-8')

# Example usage
def create_payment_request(amount, card_number, exp_date, cvc, terminal_id, test_mode=True):
    """
    Create a complete payment request
    
    Returns:
        dict: Complete payment request ready to be sent
    """
    cryptogram = create_cryptogram(card_number, exp_date, cvc, terminal_id, test_mode)
    
    return {
        "amount": amount,
        "currency": "KZT",
        "name": "TEST USER",
        "cryptogram": cryptogram,
        "invoiceId": "123456789",  # Should be generated uniquely
        "description": "test payment",
        "email": "test@test.com",
        "phone": "77777777777",
        "cardSave": True,
        "postLink": "https://your-test-site.com/callback",
        "failurePostLink": "https://your-test-site.com/callback/failure"
    }

# Example of how to use it
if __name__ == "__main__":
    # Test data
    test_card = "4405639704015096"
    test_exp = "01/27"
    test_cvc = "321"
    test_terminal = "67e34d63-102f-4bd1-898e-370781d0074d"
    
    # Create payment request
    payment_request = create_payment_request(
        amount=100,
        card_number=test_card,
        exp_date=test_exp,
        cvc=test_cvc,
        terminal_id=test_terminal,
        test_mode=True
    )
    
    print("Payment Request:")
    print(json.dumps(payment_request, indent=2))