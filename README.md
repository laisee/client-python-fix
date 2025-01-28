[![Build](https://github.com/laisee/client-python-fix/actions/workflows/python-package.yml/badge.svg)](https://github.com/laisee/client-python-fix/actions/workflows/python-package.yml)
[![Ruff](https://github.com/laisee/client-python-fix/actions/workflows/rufflint.yml/badge.svg)](https://github.com/laisee/client-python-fix/actions/workflows/rufflint.yml)
[![Security Check](https://github.com/laisee/client-python-fix/actions/workflows/security-check.yml/badge.svg)](https://github.com/laisee/client-python-fix/actions/workflows/security-check.yml)

<a href="https://www.python.org/downloads/release/python-3110/">
  <img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python 3.11">
</a>
<a href="https://www.python.org/downloads/release/python-3120/">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12">
</a>
<a href="https://www.python.org/downloads/release/python-3120/">
  <img src="https://img.shields.io/badge/Python-3.13-blue.svg" alt="Python 3.13">
</a>


# Power.Trade Fix Client (Python)

This project provides a client implementation for interacting with a FIX protocol-based API over a secure connection. 

The client is capable of:
 - Connecting to Power Trade Fix server
 - Submitting new order(s)
 - Cancelling orders
 - Handling responses (e.g. heartbeat) from the server. A heartbeat message can be sent every XX seconds where XX can be configured

## Features

- **JWT Generation:** Generates JSON Web Tokens (JWT) for authenticating requests.
- **FIX Message Handling:** Constructs and sends FIX messages to the server.
- **Secure Communication:** Establishes a secure WebSocket connection to send and receive messages.
- **Message Validation:** Validates the presence of necessary fields in messages.
- **Environment Configuration:** Uses environment variables loaded from a .env file for configuration.

## Prerequisites

- Python 3.10/3.11/3.12/3.13
- Required Python packages (can be installed via `pip`):
  - `python-dotenv`
  - `pyjwt`
  - `simplefix`
  - `socket`
  - `ssl`

## TODO

- ~~Implement logging with configurable names including yymmddhhss~~
- ~~Lint the code using common tools e.g. black, ruff, isort~~
- ~~Perform security checks~~
- ~~Generate reqular heartbeat signal messages to server side~~
- ~~Add sample code for sending & cancelling Single Leg orders~~
- Add sample code for sending & cancelling multi-leg orders
- Add sample code for listening to and processing RFQs
- Handle switching environments (test, prod) using command line args and multiple .env files

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/laisee/client-python-fix.git
   cd 'client-python-fix'

2. **Install required python libraries:**
   ```sh
   pip install -r requirements.txt 

3. **Generate API Keys**
   This is done at Power Trade UI under URL 'https://app.power.trade/api-keys'
   N.B. make sure to select "Fix API" as the API key Type and select "Order Entry/Cancel on Disconnect" if orders should be automatically cancelled when Fix session is closed or network disconnect happens.

![image](https://github.com/user-attachments/assets/b700afb6-24ad-4bf6-b28d-fc99380372a3)
  
4. **Configure the runtime environment using .env file**
   ```sh
   touch .env
   ```
   open .env file with nano or vi editors
   update settings for API Key and other values
 
6. **Configure a certificate for PowerTrade API endpoint"

   Generate a certificate for the API endpoint by inspecting & downloading public key cert from API Url e.g. api.wss.test.power.trade

   Copy the certificate contents to a file which is typically named as "cert.crt", but can be called anything.

   The cert file name can be added to the .env file using the CERTFILE_NAME variable, see example below.
   ```sh
   # Cert File location
   CERTFILE_LOCATION='cert.crt'
   ```
 
8. **Execute the client**

   Execute sample client with Python at command line:
   ```sh
   python client.py
   ```
   Review client actions as it executes logon to server, adds a new order, cancels the order while awaiting response(s).

   A sleep action allows time to review the new order on system via API or UI before it's cancelled. 
