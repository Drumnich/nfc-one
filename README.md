# One Desktop App

## Setup

1. Install Python 3.9+ (https://www.python.org/downloads/)
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Make sure your backend API is running (Flask server on http://localhost:5000)
4. Plug in your NFC reader (PC/SC compatible, e.g., ACR122U)

## Launch

```sh
python main.py
```

## Features
- Login with your account
- Scan NFC cards and add them to your dashboard
- (Planned) Assign names, block, and delete cards
- (Planned) Sync with backend and mobile app

---
For support, contact your admin or visit the One website.

# One - NFC Card Access Manager

A desktop application for managing and tracking access points for your NFC card.

## Features
- View all access points associated with your NFC card
- Add new access points
- Rename existing access points
- Support for MIFARE Classic cards (with future support for MIFARE DESFire)

## Requirements
- Python 3.8 or higher
- NFC card reader (USB contactless reader)
- MIFARE Classic NFC card

## Installation
1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Connect your NFC card reader to your computer
2. Run the application:
   ```bash
   python main.py
   ```
3. Place your NFC card on the reader to view its access points
4. Use the interface to manage your access points

## Note
This application currently supports MIFARE Classic cards. Support for MIFARE DESFire will be added in future updates. 