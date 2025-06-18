from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Signal
import requests
import os

class LoginWindow(QDialog):
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("One - Login")
        self.setMinimumWidth(320)
        layout = QVBoxLayout()

        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password.")
            return
        # Call backend API for authentication
        api_url = os.getenv("API_URL", "http://localhost:5000/api/login")
        try:
            response = requests.post(api_url, json={"email": email, "password": password})
            if response.status_code == 200:
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid credentials or server error.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not connect to server: {e}") 