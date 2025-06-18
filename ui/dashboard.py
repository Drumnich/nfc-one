from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QHBoxLayout, QMessageBox
from ui.nfc import NFCReader

class DashboardWindow(QMainWindow):
    def __init__(self, user_email):
        super().__init__()
        self.setWindowTitle(f"One - Dashboard ({user_email})")
        self.setMinimumSize(600, 400)
        central = QWidget()
        layout = QVBoxLayout()

        self.info_label = QLabel(f"Logged in as: {user_email}")
        layout.addWidget(self.info_label)

        self.card_list = QListWidget()
        layout.addWidget(self.card_list)

        btn_row = QHBoxLayout()
        self.add_card_btn = QPushButton("Add Card (Scan)")
        self.delete_card_btn = QPushButton("Delete Card")
        self.block_card_btn = QPushButton("Block Card")
        btn_row.addWidget(self.add_card_btn)
        btn_row.addWidget(self.delete_card_btn)
        btn_row.addWidget(self.block_card_btn)
        layout.addLayout(btn_row)

        central.setLayout(layout)
        self.setCentralWidget(central)

        self.nfc = NFCReader()
        self.add_card_btn.clicked.connect(self.scan_and_add_card)

        readers = self.nfc.list_readers()
        if not readers:
            QMessageBox.critical(self, "NFC Reader", "No NFC reader detected. Please connect a reader and restart the app.")
        else:
            self.info_label.setText(f"Logged in as: {user_email}\nNFC Reader: {readers[0]}")

    def scan_and_add_card(self):
        uid, error = self.nfc.read_card_uid()
        if uid:
            self.card_list.addItem(f"Card UID: {uid}")
        else:
            QMessageBox.warning(self, "NFC Error", error or "No card detected or reader not found.") 