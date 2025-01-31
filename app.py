from flask import Flask, request, redirect, render_template_string
import requests
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import uuid

app = Flask(__name__)

# Configuration
TEST_MODE = True
MERCHANT_TERMINAL_ID = "67e34d63-102f-4bd1-898e-370781d0074d"
CLIENT_ID = "test"
CLIENT_SECRET = "yF587AV9Ms94qN2QShFzVR3vFnWkhjbAK3sG"
YOUR_DOMAIN = "https://your-domain.com"  # Замените на ваш домен

# URLs
TEST_URLS = {
    'oauth': 'https://testoauth.homebank.kz/epay2/oauth2/token',
    'payment': 'https://testepay.homebank.kz/api/payment/cryptopay',
    'public_key': 'https://testepay.homebank.kz/api/public.rsa'
}

PROD_URLS = {
    'oauth': 'https://epay-oauth.homebank.kz/oauth2/token',
    'payment': 'https://epay-api.homebank.kz/payment/cryptopay',
    'public_key': 'https://epay-api.homebank.kz/public.rsa'
}

def get_urls():
    return TEST_URLS if TEST_MODE else PROD_URLS

def get_access_token(amount, invoice_id=None):
    """Получение токена доступа"""
    if invoice_id is None:
        invoice_id = str(uuid.uuid4().int)[:15]
        
    data = {
        "grant_type": "client_credentials",
        "scope": "webapi usermanagement email_send verification statement statistics payment",
        "invoiceID": invoice_id,
        "client_id": "test",
        "secret_hash": "JDKCNDDGGDTPSKJD",
        "amount": amount,
        "currency": "KZT",
        "client_secret": "yF587AV9Ms94qN2QShFzVR3vFnWkhjbAK3sG",
        "terminal": "67e34d63-102f-4bd1-898e-370781d0074d"
    }
    
    response = requests.post("https://testoauth.homebank.kz/epay2/oauth2/token", data=data)
    print(response.json()['access_token'], invoice_id)
    return response.json()['access_token'], invoice_id

def get_public_key():
    """Получение публичного ключа"""
    response = requests.get(get_urls()['public_key'])
    return RSA.importKey(response.content)

def create_cryptogram(card_number, exp_date, cvc):
    """Создание криптограммы"""
    crypto_data = {
        "hpan": card_number.replace(' ', ''),
        "expDate": exp_date.replace('/', ''),
        "cvc": cvc,
        "terminalId": MERCHANT_TERMINAL_ID
    }
    
    json_data = json.dumps(crypto_data, separators=(',', ':'))
    public_key = get_public_key()
    cipher = PKCS1_v1_5.new(public_key)
    encrypted_data = cipher.encrypt(json_data.encode('utf-8'))
    return base64.b64encode(encrypted_data).decode('utf-8')
def make_payment_request(amount, cryptogram, customer_data, invoice_id,access_token):
    """Выполнение платежного запроса"""
    payment_data = {
        "amount": amount,
        "currency": "KZT",
        "name": customer_data['name'],
        "cryptogram": cryptogram,
        "invoiceId": invoice_id,  # Используем тот же invoice_id что и в токене
        "description": "Payment for order " + invoice_id,
        "accountId": customer_data.get('account_id', ''),
        "email": customer_data['email'],
        "phone": customer_data['phone'],
        "cardSave": True,
        "postLink": f"{YOUR_DOMAIN}/payment/callback",
        "failurePostLink": f"{YOUR_DOMAIN}/payment/callback/failure",
        "secure3D": True  
    }
    
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.post(
        get_urls()['payment'],
        json=payment_data,
        headers=headers
    )
    
    return response.json()

# HTML шаблон для формы оплаты
PAYMENT_FORM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Payment Form</title>
    <style>
        .container { max-width: 500px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input { width: 100%; padding: 8px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; }
    </style>
</head>
<body>
    <div class="container">
        <form method="POST" action="/process-payment">
            <div class="form-group">
                <label>Card Number</label>
                <input type="text" name="card_number" required pattern="[0-9 ]{16,19}">
            </div>
            <div class="form-group">
                <label>Expiry Date (MM/YY)</label>
                <input type="text" name="exp_date" required pattern="[0-9]{2}/[0-9]{2}">
            </div>
            <div class="form-group">
                <label>CVC</label>
                <input type="text" name="cvc" required pattern="[0-9]{3}">
            </div>
            <div class="form-group">
                <label>Amount (KZT)</label>
                <input type="number" name="amount" required>
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Phone</label>
                <input type="tel" name="phone" required>
            </div>
            <div class="form-group">
                <label>Name</label>
                <input type="text" name="name" required>
            </div>
            <button type="submit">Pay</button>
        </form>
    </div>
</body>
</html>
"""

# HTML шаблон для 3D Secure формы
SECURE_3D_TEMPLATE = """
<!DOCTYPE html>
<html>
<body onload="document.forms[0].submit();">
    <form action="{{ action }}" method="POST">
        <input type="hidden" name="PaReq" value="{{ pa_req }}">
        <input type="hidden" name="MD" value="{{ md }}">
        <input type="hidden" name="TermUrl" value="{{ term_url }}">
    </form>
    <div align="center">
        <h1>
            Redirecting to secure payment page...<br>
            Перенаправление на защищенную страницу оплаты...<br>
        </h1>
    </div>
</body>
</html>
"""

@app.route('/')
def show_payment_form():
    """Показать форму для ввода данных карты"""
    return render_template_string(PAYMENT_FORM_TEMPLATE)

@app.route('/process-payment', methods=['POST'])
def process_payment():
    """Обработка данных карты и инициация платежа"""
    try:
        amount = float(request.form['amount'])
        
        # Сначала получаем токен и invoice_id
        access_token, invoice_id = get_access_token(amount)
        
        # Создание криптограммы
        cryptogram = create_cryptogram(
            request.form['card_number'],
            request.form['exp_date'],
            request.form['cvc']
        )
        
        # Данные клиента
        customer_data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'phone': request.form['phone']
        }
        print(customer_data)
        # Выполнение платежного запроса с тем же invoice_id
        response = make_payment_request(
            amount,
            cryptogram,
            customer_data,
            invoice_id,
            access_token
        )
        print(response)
        # Проверка на 3D Secure
        if 'secure3D' in response and response['secure3D'] is not None:
            return render_template_string(
                SECURE_3D_TEMPLATE,
                action=response['secure3D']['action'],
                pa_req=response['secure3D']['paReq'],
                md=response['secure3D']['md'],
                term_url=f"{YOUR_DOMAIN}/payment/callback"
            )
        else:
            return handle_successful_payment(response)
            
    except Exception as e:
        return f"Error: {str(e)}", 400
@app.route('/payment/callback', methods=['POST'])
def payment_callback():
    """Обработка callback'а после 3D Secure"""
    try:
        pa_res = request.form.get('PaRes')
        md = request.form.get('MD')
        
        # Подтверждение платежа после 3D Secure
        confirm_data = {
            "PaRes": pa_res,
            "MD": md
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {get_access_token()}'
        }
        
        response = requests.post(
            f"{get_urls()['payment']}/confirm",
            json=confirm_data,
            headers=headers
        )
        
        return handle_successful_payment(response.json())
        
    except Exception as e:
        return f"Error in callback: {str(e)}", 400

@app.route('/payment/callback/failure', methods=['POST'])
def payment_failure():
    """Обработка неуспешных платежей"""
    # Здесь ваша логика обработки неуспешных платежей
    return "Payment failed", 400

def handle_successful_payment(response):
    """Обработка успешного платежа"""
    # Здесь ваша логика обработки успешного платежа
    return f"""
    Payment successful!<br>
    Reference: {response.get('reference', '')}<br>
    Invoice ID: {response.get('invoiceId', '')}<br>
    Status: {response.get('status', '')}
    """

if __name__ == '__main__':
    app.run(debug=True)