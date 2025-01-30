import json
import base64
import requests
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes

# 1. Получаем публичный ключ с сервера
response = requests.get("https://testepay.homebank.kz/api/public.rsa")
public_key_pem = response.text

# 2. Загружаем публичный ключ
# public_key = serialization.load_pem_public_key(public_key_pem.encode())

# # 3. Исходные данные для шифрования
# data = {
#     "hpan": "4003032704547597",
#     "expDate": "1022",
#     "cvc": "636",
#     "terminalId": "67e34d63-102f-4bd1-898e-370781d0074d"
# }

# # 4. Преобразуем данные в JSON-строку
# data_json = json.dumps(data, separators=(',', ':'))  # Убираем пробелы

# # 5. Шифруем данные
# encrypted_data = public_key.encrypt(
#     data_json.encode(),
#     padding.OAEP(
#         mgf=padding.MGF1(algorithm=hashes.SHA256()),
#         algorithm=hashes.SHA256(),
#         label=None
#     )
# )

# # 6. Кодируем зашифрованные данные в Base64
# cryptogram = base64.b64encode(encrypted_data).decode('utf-8')

# print("Зашифрованная криптограмма:", encrypted_data)


private_key = serialization.load_pem_private_key(public_key_pem.encode(), password=None)

# Ваша зашифрованная криптограмма (Base64)
encrypted_data_base64 = "UhYXAhYGeFA6srEVJ2V8Jtnnz6NzRwy8QDkCvEmJOcC6KyBP/Ce4SUM0A0My1zS1Iiur6AF0ajJwdi31EvrkRDBvzl2iLVKzvuAyusc5KuGpgxRhc6WXDhKkHV7J5Oew8uPMOfVbmXZ+Ypihos5ynSX7TnqQg1ImAmEISBxT+YU7jY68uxGhlehYMJ0lgS1Req4Z0BwCExBL2lwo05lmSMed69bEdBX552ue13zXjvTKIMrVj70hXIppXnxAE7haJfObuQzx2Ox+wM087kFPXfDX8Udlc6iRP2TxnRj7R1GnCTLvf3xlVU9ELzK+j91SPBQTvyEeyEvGMunjRch8lGXlogQreFSZmC5FUpfdfw6jYhl6lizUZYZzroN6/i5MILtV0US8zPFZTfozrCj8cvqw+J2W7yBywDiFoZG1teLDMIKIqTvkrmRL++Ji0psdHXl0z0ng/d0yTxzcBpPZ5V8VfNOexJJRZQUXBQqygAqqYninku/ls1NuTRMPeveyrgSMjQUVKU2W1izXdSreSdvaOio+1HJHNCZDwNn9yheTzbmuUsl5lhnsUGNT5gzMuYje8VfRYpsvG3Syz6nOijprG1wL3L/p5B/SZGrtaMMg/OdbD3mUWCSmat/V2v9RKHaeo5OHMnaVMTY5Tsqwa5JKBRP4ztRcjkjMRCBvS8c="

# Декодируем Base64
encrypted_data = base64.b64decode(encrypted_data_base64)

# Расшифровываем данные с использованием закрытого ключа
decrypted_data = private_key.decrypt(
    encrypted_data,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Преобразуем расшифрованные данные обратно в строку
decrypted_str = decrypted_data.decode('utf-8')

print("Расшифрованные данные:", decrypted_str)