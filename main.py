import sys
import os
from PySide6.QtWidgets import QApplication, QDialog
from dotenv import load_dotenv
from ui.login import LoginWindow
from ui.dashboard import DashboardWindow

if __name__ == "__main__":
    load_dotenv()
    app = QApplication(sys.argv)
    login = LoginWindow()
    if login.exec() == QDialog.Accepted:
        dashboard = DashboardWindow(login.email_input.text())
        dashboard.show()
        sys.exit(app.exec()) 