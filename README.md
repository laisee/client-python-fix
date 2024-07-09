[![CI](https://github.com/laisee/client-python-fix/actions/workflows/python-package.yml/badge.svg)](https://github.com/laisee/client-python-fix/actions/workflows/python-package.yml)

# Power.Trade Fix client.py

This project provides a client implementation for interacting with a FIX protocol-based API over a secure WebSocket connection. 

The client is capable of logging in, sending orders, and receiving responses from the server.

## Features

- **JWT Generation:** Generates JSON Web Tokens (JWT) for authenticating requests.
- **FIX Message Handling:** Constructs and sends FIX messages to the server.
- **WebSocket Communication:** Establishes a secure WebSocket connection to send and receive messages.
- **Message Validation:** Validates the presence of necessary fields in messages.
- **Environment Configuration:** Uses environment variables loaded from a .env file for configuration.

## Prerequisites

- Python 3.x
- Required Python packages (can be installed via `pip`):
  - `python-dotenv`
  - `pyjwt`
  - `simplefix`
  - `socket`
  - `ssl`

## TODO

- ~~Implement logging~~
- ~~Lint the code~~
- ~~Perform security checks~~
- Handle switching environments (test, prod) using command line args and multiple .env files
- Add sample code for cancelling orders, sending multi-leg orders, listening for and processing RFQs
- Generate reqular heartbeat signal messages to server side

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/laisee/client-python-fix.git
   cd 'client-python-fix'

2. **Install required python libraries:**
   ```sh
   pip install -r requirements.txt 

3. **Execute the client**

   Process logon to server, add new order and await response(s) for order confirmation 
