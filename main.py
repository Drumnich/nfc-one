import sys
import sqlite3
import hashlib
import bcrypt
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QListWidget, QLineEdit,
                            QLabel, QMessageBox, QFrame, QGroupBox, QScrollArea,
                            QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem,
                            QHeaderView, QDialog, QFormLayout, QListWidgetItem)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, Property, QEvent, QPointF
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QFontDatabase, QPainter, QLinearGradient, QBrush, QPixmap, QMovie
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QGraphicsBlurEffect
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException, CardConnectionException
from smartcard.CardMonitoring import CardMonitor, CardObserver
from datetime import datetime
import psycopg2
import os
import math

# Configure logging with different levels for file and console
file_handler = logging.FileHandler('nfc_card_manager.log')
file_handler.setLevel(logging.DEBUG)  # Detailed logging to file
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(console_handler)

# Card-specific timeout settings (in seconds)
CARD_TIMEOUTS = {
    "JCOP 2.4.1": 2.0,
    "JCOP 2.4": 2.0,
    "JCOP 3": 1.5,
    "JCOP 3 SECID": 1.5,
    "MIFARE DESFire": 1.0,
    "MIFARE Classic": 1.0,
    "Unknown": 3.0  # Longer timeout for unknown cards
}

# Maximum retry attempts for card operations
MAX_RETRIES = 3

class AnimatedGradientBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gradient_pos = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def animate(self):
        self.gradient_pos += 0.002
        if self.gradient_pos > 1.0:
            self.gradient_pos = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor(0, 210, 255))
        grad.setColorAt(0.5 + 0.5 * self.gradient_pos, QColor(120, 0, 255))
        grad.setColorAt(1.0, QColor(0, 255, 200))
        painter.fillRect(rect, QBrush(grad))
        super().paintEvent(event)

class GlassCard(QWidget):
    def __init__(self, color, icon_path, title, parent=None):
        super().__init__(parent)
        self.color = color
        self.icon_path = icon_path
        self.title = title
        self.setFixedSize(260, 160)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._tilt = 0
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self._tilt = 10
        self.update()
    def leaveEvent(self, event):
        self._tilt = 0
        self.update()
    def mouseMoveEvent(self, event):
        # 3D tilt effect based on mouse position
        x = event.position().x() - self.width()/2
        self._tilt = max(-15, min(15, x/10))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.save()
        painter.translate(rect.center())
        painter.rotate(self._tilt)
        painter.translate(-rect.center())
        # Glassmorphic card
        painter.setBrush(QColor(self.color.red(), self.color.green(), self.color.blue(), 120))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 32, 32)
        # Card icon
        if self.icon_path:
            pix = QPixmap(self.icon_path)
            if not pix.isNull():
                painter.drawPixmap(30, 30, 48, 48, pix)
        # Card title
        painter.setPen(QColor(255,255,255,220))
        painter.setFont(QFont('Arial', 18, QFont.Bold))
        painter.drawText(rect.adjusted(0, 100, 0, 0), Qt.AlignHCenter, self.title)
        painter.restore()
        super().paintEvent(event)

class CardCarousel(QWidget):
    def __init__(self, cards, parent=None):
        super().__init__(parent)
        self.cards = cards
        self.offset = 0
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self._drag_start = None

    def mousePressEvent(self, event):
        self._drag_start = event.position().x()
    def mouseMoveEvent(self, event):
        if self._drag_start is not None:
            dx = event.position().x() - self._drag_start
            self.offset = max(-((len(self.cards)-1)*280), min(0, self.offset + dx))
            self._drag_start = event.position().x()
            self.update()
    def mouseReleaseEvent(self, event):
        self._drag_start = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        x = w//2 - 130 + self.offset
        for i, card in enumerate(self.cards):
            painter.save()
            painter.translate(x + i*280, h//2 - 80)
            card.render(painter)
            painter.restore()
        super().paintEvent(event)

class GlassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet('background: transparent;')

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            painter.setBrush(QColor(255, 255, 255, 60))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 24, 24)
        except Exception as e:
            print(f"GlassWidget paint error: {e}")
        super().paintEvent(event)

class AnimatedCard3D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.anim = QPropertyAnimation(self, b"angle")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0)
        self.anim.setEndValue(180)
        self.anim.setLoopCount(-1)
        self.anim.start()
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)

    def getAngle(self):
        return self._angle
    def setAngle(self, value):
        self._angle = value
        self.update()
    angle = Property(float, getAngle, setAngle)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.translate(rect.center())
        painter.rotate(self._angle)
        painter.translate(-rect.center())
        # Card body
        painter.setBrush(QColor(0, 210, 255, 220))
        painter.setPen(QColor(0, 120, 180, 180))
        painter.drawRoundedRect(rect.adjusted(20, 20, -20, -20), 24, 24)
        # Card chip
        painter.setBrush(QColor(255, 215, 0, 180))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect.center().x()-18, rect.center().y()-12, 36, 24, 8, 8)
        # Card text
        painter.setPen(QColor(255,255,255,220))
        painter.setFont(QFont('Arial', 18, QFont.Bold))
        painter.drawText(rect.adjusted(0, 60, 0, 0), Qt.AlignHCenter, "NFC CARD")
        super().paintEvent(event)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.register_button = QPushButton("Register")
        self.login_button.clicked.connect(self.accept)
        self.register_button.clicked.connect(self.register)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                min-width: 300px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QLabel {
                color: #424242;
                font-size: 13px;
            }
        """)
        
    def register(self):
        self.done(2)  # Custom return code for registration

    def showEvent(self, event):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        super().showEvent(event)

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.accept)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.register_button)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                min-width: 300px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QLabel {
                color: #424242;
                font-size: 13px;
            }
        """)

    def showEvent(self, event):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        super().showEvent(event)

class NFCCardObserver(CardObserver):
    def __init__(self, handler):
        self.handler = handler
        
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        for card in addedcards:
            self.handler.handle_card_inserted(card)
        for card in removedcards:
            self.handler.handle_card_removed()

class NFCCardManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFC Card Access Manager")
        self.setMinimumSize(1024, 768)
        self.current_user = None
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                font-size: 13px;
                background-color: #FFFFFF;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QLineEdit::placeholder {
                color: #9E9E9E;
            }
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FFFFFF;
                font-size: 13px;
                padding: 5px;
                color: #000000;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #F5F5F5;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                color: #1565C0;
                border-radius: 4px;
            }
            QLabel {
                font-size: 13px;
                color: #424242;
            }
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F5F5F5;
                color: #757575;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTableWidget {
                gridline-color: #F5F5F5;
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 10px;
                border: none;
                font-weight: bold;
                color: #424242;
            }
            QTableWidget::item {
                padding: 5px;
                color: #000000;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F5F5F5;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }
        """)
        
        # Initialize variables
        self.reader = None
        self.current_card = None
        self.card_history = []
        self.last_readings = []
        self.cardmonitor = None
        self.cardobserver = None
        
        # Initialize database
        self.init_database()
        
        # Setup UI
        self.setup_ui()
        
        # Show login dialog
        self.show_login()
        
        # Start NFC reader
        self.start_nfc_reader()
        
        # Add animated gradient background
        self.bg_widget = AnimatedGradientBackground(self)
        self.bg_widget.setGeometry(self.geometry())
        self.bg_widget.lower()
        self.installEventFilter(self)

        # Set custom font for the app (disable for now)
        # app_font = QFont(font_family, 12)
        # QApplication.instance().setFont(app_font)
        
    def get_db_connection(self):
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres.xqyhrcznzkwkvgfcuebp",
            password="Y@rze2002",
            host="aws-0-eu-west-3.pooler.supabase.com",
            port="6543"
        )
        cursor = conn.cursor()
        return conn, cursor

    def init_database(self):
        """Initialize the database schema"""
        conn, cursor = self.get_db_connection()
        try:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add new columns if they don't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
                conn.commit()
            except psycopg2.Error:
                conn.rollback()  # Column already exists
                
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN phone TEXT')
                conn.commit()
            except psycopg2.Error:
                conn.rollback()  # Column already exists
                
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                conn.commit()
            except psycopg2.Error:
                conn.rollback()  # Column already exists

            # Create locations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, name)
                )
            ''')
            
            # Create access points table linking cards to locations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_points (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    location_id UUID NOT NULL,
                    card_id TEXT NOT NULL,
                    access_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (location_id) REFERENCES locations (id),
                    UNIQUE(location_id, card_id)
                )
            ''')
            
            # Create card history table with custom name field
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS card_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    card_id TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    custom_name TEXT,
                    frequency TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            logging.error(f"Database initialization error: {str(e)}")
        finally:
            conn.close()
        
    def setup_ui(self):
        # Use glass panel for main content
        main_panel = GlassPanel()
        self.setCentralWidget(main_panel)
        layout = QVBoxLayout(main_panel)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header section with large modern font
        header_layout = QHBoxLayout()
        self.user_label = QLabel("")
        self.user_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #00d2ff;")
        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet("background-color: #F44336; max-width: 100px; font-size: 16px; border-radius: 12px;")
        self.logout_button.clicked.connect(self.logout)
        self.profile_button = QPushButton("Profile")
        self.profile_button.setStyleSheet("background-color: #fff; color: #00d2ff; border-radius: 12px; font-size: 16px; border: 2px solid #00d2ff;")
        self.profile_button.clicked.connect(self.show_profile)
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()
        header_layout.addWidget(self.profile_button)
        header_layout.addWidget(self.logout_button)
        layout.addLayout(header_layout)

        # Animated 3D card for NFC status
        card3d = AnimatedCard3D()
        layout.addWidget(card3d, alignment=Qt.AlignHCenter)

        # Card Status Section with rename capability
        status_group = QGroupBox("Card Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Initializing reader...")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #666666;
            padding: 10px;
            background-color: #F5F5F5;
            border-radius: 6px;
        """)
        status_layout.addWidget(self.status_label)
        
        # Add card name editing
        name_layout = QHBoxLayout()
        self.card_name_input = QLineEdit()
        self.card_name_input.setPlaceholderText("Enter card name")
        self.card_name_input.setEnabled(False)
        rename_card_button = QPushButton("Rename Card")
        rename_card_button.clicked.connect(self.rename_card)
        rename_card_button.setEnabled(False)
        self.card_name_input.textChanged.connect(
            lambda: rename_card_button.setEnabled(bool(self.card_name_input.text().strip()))
        )
        
        name_layout.addWidget(self.card_name_input)
        name_layout.addWidget(rename_card_button)
        status_layout.addLayout(name_layout)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Tab widget for different sections
        tab_widget = QTabWidget()
        
        # Access Points Tab
        access_tab = QWidget()
        access_layout = QVBoxLayout(access_tab)
        access_layout.setSpacing(15)
        
        # Locations Group
        locations_group = QGroupBox("Locations")
        locations_layout = QVBoxLayout()
        
        # Add location section
        add_location_layout = QHBoxLayout()
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter location name (e.g., Home, Office)")
        self.location_description = QLineEdit()
        self.location_description.setPlaceholderText("Enter location description (optional)")
        add_location_button = QPushButton("Add Location")
        add_location_button.clicked.connect(self.add_location)
        
        add_location_layout.addWidget(self.location_input)
        add_location_layout.addWidget(self.location_description)
        add_location_layout.addWidget(add_location_button)
        locations_layout.addLayout(add_location_layout)
        
        # Locations list
        self.locations_list = QListWidget()
        self.locations_list.itemSelectionChanged.connect(self.on_location_selected)
        locations_layout.addWidget(self.locations_list)
        
        locations_group.setLayout(locations_layout)
        access_layout.addWidget(locations_group)
        
        # Cards for Location Group
        cards_group = QGroupBox("Cards for Selected Location")
        cards_layout = QVBoxLayout()
        
        # Cards list
        self.cards_list = QListWidget()
        cards_layout.addWidget(self.cards_list)
        
        # Add current card to location
        add_card_layout = QHBoxLayout()
        add_card_button = QPushButton("Add Current Card")
        add_card_button.clicked.connect(self.add_card_to_location)
        remove_card_button = QPushButton("Remove Selected Card")
        remove_card_button.clicked.connect(self.remove_card_from_location)
        remove_card_button.setStyleSheet("background-color: #f44336;")
        
        add_card_layout.addWidget(add_card_button)
        add_card_layout.addWidget(remove_card_button)
        cards_layout.addLayout(add_card_layout)
        
        cards_group.setLayout(cards_layout)
        access_layout.addWidget(cards_group)
        
        tab_widget.addTab(access_tab, "Access Points")
        
        # Card History Tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        history_group = QGroupBox("Card History")
        history_inner_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(
            ["Card Name", "Card ID", "Type", "First Seen", "Last Seen"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Make the table read-only
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        history_inner_layout.addWidget(self.history_table)
        history_group.setLayout(history_inner_layout)
        history_layout.addWidget(history_group)
        
        tab_widget.addTab(history_tab, "Card History")
        
        layout.addWidget(tab_widget)
        
        # Add animated button hover/press effects globally
        self.setStyleSheet(self.styleSheet() + """
            QPushButton {
                font-size: 15px;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #00d2ff;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0088aa;
                color: #fff;
            }
            QTabWidget::pane {
                border-radius: 18px;
                background: rgba(255,255,255,0.7);
            }
            QGroupBox {
                border-radius: 18px;
                background: rgba(255,255,255,0.5);
                font-size: 18px;
                font-weight: 600;
            }
        """)
        
    def show_login(self):
        """Show login dialog and handle authentication"""
        while True:
            dialog = LoginDialog(self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                username = dialog.username_input.text()
                password = dialog.password_input.text()
                
                if self.authenticate_user(username, password):
                    self.current_user = username
                    self.user_label.setText(f"Welcome, {username}!")
                    self.load_card_history()
                    break
                else:
                    QMessageBox.warning(self, "Error", "Invalid username or password")
            elif result == 2:  # Register
                self.show_register()
            else:
                sys.exit()
                
    def show_register(self):
        """Show registration dialog"""
        dialog = RegisterDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            username = dialog.username_input.text()
            password = dialog.password_input.text()
            confirm_password = dialog.confirm_password_input.text()
            
            if password != confirm_password:
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
                
            if self.register_user(username, password):
                QMessageBox.information(self, "Success", "Registration successful! Please login.")
            else:
                QMessageBox.warning(self, "Error", "Username already exists")
                
    def register_user(self, username, password):
        """Register a new user"""
        conn, cursor = self.get_db_connection()
        try:
            # Check if username already exists (case-insensitive check)
            cursor.execute('SELECT username FROM users WHERE lower(username) = lower(%s)', (username,))
            if cursor.fetchone():
                return False  # Username already exists
            
            # Store all information exactly as entered
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                         (username, password_hash.decode('utf-8')))  # Store hash as string
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()
            
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        conn, cursor = self.get_db_connection()
        try:
            # Use case-insensitive search but return exact stored values
            cursor.execute('''
                SELECT username, password_hash, email, phone 
                FROM users 
                WHERE lower(username) = lower(%s)
            ''', (username,))
            result = cursor.fetchone()
            
            if result:
                stored_hash = result[1]
                try:
                    # Convert password to bytes and verify
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        # Store all user information exactly as it was entered
                        self.current_user = result[0]  # Exact username
                        self.current_user_email = result[2]  # Exact email
                        self.current_user_phone = result[3]  # Exact phone
                        return True
                except Exception as e:
                    logging.error(f"Password verification error: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return False
        finally:
            conn.close()
        
    def logout(self):
        """Handle user logout"""
        self.current_user = None
        self.current_card = None
        self.card_history.clear()
        self.last_readings.clear()
        self.locations_list.clear()  # Clear locations list
        self.cards_list.clear()  # Clear cards list
        self.history_table.setRowCount(0)
        self.show_login()

    def load_card_history(self):
        """Load card history for current user"""
        if not self.current_user:
            return
            
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('''
                SELECT COALESCE(custom_name, 'Unnamed Card'), card_id, card_type, first_seen, last_seen 
                FROM card_history 
                WHERE user_id = (SELECT id FROM users WHERE username = %s)
                ORDER BY last_seen DESC
            ''', (self.current_user,))
            
            self.history_table.setRowCount(0)
            for row in cursor.fetchall():
                row_position = self.history_table.rowCount()
                self.history_table.insertRow(row_position)
                
                for col, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make item read-only
                    self.history_table.setItem(row_position, col, item)
        finally:
            conn.close()

    def update_status(self, message, status_type="info"):
        """Update status label with appropriate styling"""
        style = {
            "info": """
                color: #666666;
                background-color: #F5F5F5;
            """,
            "success": """
                color: #2E7D32;
                background-color: #E8F5E9;
            """,
            "error": """
                color: #C62828;
                background-color: #FFEBEE;
            """,
            "warning": """
                color: #F57C00;
                background-color: #FFF3E0;
            """
        }
        
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            font-size: 14px;
            padding: 10px;
            border-radius: 6px;
            {style.get(status_type, style["info"])}
        """)

    def check_for_card(self):
        """Method called by timer to check for card presence"""
        if not self.reader or not self.current_user:
            return
            
        try:
            connection = self.reader.createConnection()
            connection.connect()
            
            # Try to get card ID and type
            card_id, card_type = self.get_card_uid(connection)
            
            if card_id:
                if not self.current_card or self.current_card != card_id:
                    self.current_card = card_id
                    logging.info(f"New card detected - ID: {card_id}, Type: {card_type}")
                    
                    # Update card history
                    self.update_card_history(card_id, card_type)
                    
                    # Get card name
                    card_name = self.get_card_name(card_id)
                    if card_name:
                        self.card_name_input.setText(card_name)
                        logging.info(f"Card name found: {card_name}")
                    else:
                        self.card_name_input.clear()
                        logging.debug("No custom name found for card")
                    
                    # Enable card name input
                    self.card_name_input.setEnabled(True)
                    
                    # Update status with name if available
                    status_text = f"Card detected - ID: {card_id[:8]}... ({card_type})"
                    if card_name:
                        status_text = f"{card_name} - {status_text}"
                    
                    self.update_status(status_text, "success")
                    self.load_locations()
            
        except CardConnectionException as e:
            # This is an expected state when no card is present
            if self.current_card:  # Only log and update UI if state changed
                logging.debug("Card removed from reader")
                self.current_card = None
                self.last_readings.clear()
                self.update_status("Please place a card on the reader", "info")
                self.cards_list.clear()
                self.card_name_input.setEnabled(False)
                self.card_name_input.clear()
        except Exception as e:
            error_msg = str(e)
            # Only log unexpected errors
            if not "no smart card inserted" in error_msg.lower():
                logging.error(f"Error during card check: {error_msg}")
                
                # Handle specific error cases
                if "timeout" in error_msg.lower():
                    self.update_status("Card communication timeout. Please try again.", "warning")
                elif "connection" in error_msg.lower():
                    self.update_status("Reader connection error. Please check the reader.", "error")
                elif "permission" in error_msg.lower():
                    self.update_status("Permission denied accessing the reader. Please check your system settings.", "error")
                else:
                    self.update_status(f"Error reading card: {error_msg}", "error")

    def update_card_history(self, card_id, card_type):
        """Update card history for the current user"""
        if not self.current_user:
            return
            
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('SELECT id FROM users WHERE username = %s', (self.current_user,))
            user_id = cursor.fetchone()[0]
            
            # Check if card exists in history
            cursor.execute('''
                SELECT id FROM card_history 
                WHERE user_id = %s AND card_id = %s
            ''', (user_id, card_id))
            
            if cursor.fetchone():
                # Update last_seen
                cursor.execute('''
                    UPDATE card_history 
                    SET last_seen = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND card_id = %s
                ''', (user_id, card_id))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO card_history (user_id, card_id, card_type) 
                    VALUES (%s, %s, %s)
                ''', (user_id, card_id, card_type))
            
            conn.commit()
            self.load_card_history()
        finally:
            conn.close()

    def load_locations(self):
        """Load all locations for current user"""
        if not self.current_user:
            logging.warning("Attempted to load locations without user login")
            return
            
        self.locations_list.clear()
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('''
                SELECT name, description 
                FROM locations 
                WHERE user_id = (SELECT id FROM users WHERE username = %s)
                ORDER BY name
            ''', (self.current_user,))
            
            locations = cursor.fetchall()
            logging.debug(f"Found {len(locations)} locations for user {self.current_user}")
            
            for name, description in locations:
                item = QListWidgetItem(name)
                if description:
                    item.setToolTip(description)
                self.locations_list.addItem(item)
                
            if not locations:
                logging.info("No locations found for current user")
                
        except psycopg2.Error as e:
            error_msg = str(e)
            logging.error(f"Error loading locations: {error_msg}")
            self.update_status(f"Error loading locations: {error_msg}", "error")
        finally:
            conn.close()

    def load_cards_for_location(self):
        """Load all cards associated with selected location"""
        if not self.current_user:
            return
            
        self.cards_list.clear()
        selected_items = self.locations_list.selectedItems()
        if not selected_items:
            return
            
        location_name = selected_items[0].text()
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('''
                SELECT ch.custom_name, ch.card_id, ch.card_type
                FROM access_points ap
                JOIN locations l ON ap.location_id = l.id
                JOIN card_history ch ON ap.card_id = ch.card_id
                WHERE l.name = %s AND l.user_id = (SELECT id FROM users WHERE username = %s)
                ORDER BY ch.custom_name, ch.card_id
            ''', (location_name, self.current_user))
            
            for name, card_id, card_type in cursor.fetchall():
                display_name = name if name else f"Unnamed Card ({card_id[:8]}...)"
                item = QListWidgetItem(f"{display_name} - {card_type}")
                item.setData(Qt.UserRole, card_id)
                self.cards_list.addItem(item)
        finally:
            conn.close()

    def add_location(self):
        """Add a new location"""
        if not self.current_user:
            self.update_status("Please log in first", "error")
            return
            
        name = self.location_input.text().strip()
        description = self.location_description.text().strip()
        
        if not name:
            self.update_status("Please enter a location name", "warning")
            return
            
        logging.info(f"Adding new location: {name}")
        
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('SELECT id FROM users WHERE username = %s', (self.current_user,))
            user_result = cursor.fetchone()
            
            if not user_result:
                self.update_status("User not found. Please log in again.", "error")
                return
                
            user_id = user_result[0]
            
            # Check if location already exists for this user
            cursor.execute('SELECT id FROM locations WHERE user_id = %s AND name = %s', 
                         (user_id, name))
            if cursor.fetchone():
                self.update_status(f"Location '{name}' already exists", "warning")
                return
            
            # Add the new location
            cursor.execute('''
                INSERT INTO locations (user_id, name, description)
                VALUES (%s, %s, %s)
            ''', (user_id, name, description))
            conn.commit()
            
            self.location_input.clear()
            self.location_description.clear()
            self.load_locations()
            self.update_status(f"Added location: {name}", "success")
            logging.info(f"Successfully added location: {name}")
            
        except psycopg2.Error as e:
            error_msg = str(e)
            logging.error(f"Database error while adding location: {error_msg}")
            self.update_status(f"Error adding location: {error_msg}", "error")
        finally:
            conn.close()

    def on_location_selected(self):
        """Handle location selection change"""
        self.load_cards_for_location()

    def add_card_to_location(self):
        """Add current card to selected location"""
        if not self.current_card or not self.current_user:
            QMessageBox.warning(self, "No Card", "Please place a card on the reader first.")
            return
            
        selected_items = self.locations_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Location", "Please select a location first.")
            return
            
        location_name = selected_items[0].text()
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('SELECT id FROM users WHERE username = %s', (self.current_user,))
            user_id = cursor.fetchone()[0]
            
            cursor.execute('SELECT id FROM locations WHERE user_id = %s AND name = %s',
                         (user_id, location_name))
            location_id = cursor.fetchone()[0]
            
            # Add card to location
            cursor.execute('''
                INSERT INTO access_points (user_id, location_id, card_id)
                VALUES (%s, %s, %s)
            ''', (user_id, location_id, self.current_card))
            conn.commit()
            
            self.load_cards_for_location()
            self.update_status(f"Added card to {location_name}", "success")
        except psycopg2.Error as e:
            self.update_status(f"Error adding card: {str(e)}", "error")
        finally:
            conn.close()

    def remove_card_from_location(self):
        """Remove selected card from location"""
        selected_location = self.locations_list.selectedItems()
        selected_card = self.cards_list.selectedItems()
        
        if not selected_location or not selected_card:
            return
            
        location_name = selected_location[0].text()
        card_id = selected_card[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove this card from {location_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn, cursor = self.get_db_connection()
            try:
                cursor.execute('''
                    DELETE FROM access_points 
                    WHERE card_id = %s AND location_id = (
                        SELECT id FROM locations 
                        WHERE name = %s AND user_id = (
                            SELECT id FROM users WHERE username = %s
                        )
                    )
                ''', (card_id, location_name, self.current_user))
                conn.commit()
                
                self.load_cards_for_location()
                self.update_status(f"Removed card from {location_name}", "success")
            except psycopg2.Error as e:
                self.update_status(f"Error removing card: {str(e)}", "error")
            finally:
                conn.close()

    def detect_card_frequency(self, atr):
        """Detect card frequency based on ATR"""
        atr_string = toHexString(atr) if atr else ""
        
        # This is a simplified detection - would need to be expanded based on actual cards
        if atr_string.startswith("3B 8F"):  # Example JCOP
            return "13.56 MHz"
        elif atr_string.startswith("3B 8E"):  # Example MIFARE
            return "13.56 MHz"
        elif atr_string.startswith("3B 67"):  # Example EM4100
            return "125 kHz"
        return "Unknown"

    def rename_card(self):
        """Rename the current card"""
        if not self.current_card or not self.current_user:
            return
            
        new_name = self.card_name_input.text().strip()
        if not new_name:
            return
            
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('SELECT id FROM users WHERE username = %s', (self.current_user,))
            user_id = cursor.fetchone()[0]
            
            # Update card name
            cursor.execute('''
                UPDATE card_history 
                SET custom_name = %s
                WHERE user_id = %s AND card_id = %s
            ''', (new_name, user_id, self.current_card))
            conn.commit()
            
            self.update_status(f"Card renamed to: {new_name}", "success")
            self.load_card_history()
        except psycopg2.Error as e:
            self.update_status(f"Error renaming card: {str(e)}", "error")
        finally:
            conn.close()

    def get_card_name(self, card_id):
        """Get the custom name for a card"""
        if not self.current_user or not card_id:
            return None
            
        conn, cursor = self.get_db_connection()
        try:
            cursor.execute('''
                SELECT custom_name 
                FROM card_history 
                WHERE user_id = %s AND card_id = %s
            ''', (self.current_user, card_id))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        finally:
            conn.close()

    def closeEvent(self, event):
        """Handle application close"""
        # Clear all lists before closing
        if hasattr(self, 'locations_list'):
            self.locations_list.clear()
        if hasattr(self, 'cards_list'):
            self.cards_list.clear()
        if hasattr(self, 'history_table'):
            self.history_table.setRowCount(0)
        event.accept()

    def start_nfc_reader(self):
        try:
            # Get list of available readers
            available_readers = readers()
            
            if not available_readers:
                self.update_status("No card readers found. Please connect a reader.", "error")
                return
                
            # Use the first available reader
            self.reader = available_readers[0]
            self.update_status(f"Reader ready: {self.reader}", "success")
            
        except Exception as e:
            self.update_status(f"Error initializing reader: {str(e)}", "error")

    def get_card_type(self, atr):
        """Determine card type based on ATR"""
        if not atr:
            return "Unknown"
        
        atr_string = toHexString(atr)
        logging.debug(f"Detecting card type for ATR: {atr_string}")
        
        # JCOP 3 cards (including J3R200)
        if atr_string.startswith("3B F8") or atr_string.startswith("3B FA"):
            return "JCOP 3 (J3R200)"
        # Other JCOP cards
        elif atr_string.startswith("3B 8B 80 01"):
            return "JCOP 2.4.1"
        elif atr_string.startswith("3B 88 80"):
            return "JCOP 2.4"
        elif atr_string.startswith("3B 8F 80"):
            return "JCOP 3 SECID"
        # MIFARE cards
        elif atr_string.startswith("3B 7D"):
            return "MIFARE DESFire"
        elif atr_string.startswith("3B 8E"):
            return "MIFARE Classic"
        
        return f"Unknown Card ({atr_string[:20]}...)"

    def get_card_uid(self, connection):
        """Get unique identifier from JCOP card"""
        retry_count = 0
        last_error = None
        
        while retry_count < MAX_RETRIES:
            try:
                # Get ATR first for card type identification
                atr = connection.getATR()
                card_type = self.get_card_type(atr)
                logging.info(f"Attempting to read card (Attempt {retry_count + 1}/{MAX_RETRIES})")
                logging.info(f"Card type detected: {card_type}")

                # Try to get direct UID first (most reliable method)
                get_uid_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                try:
                    response, sw1, sw2 = connection.transmit(get_uid_cmd)
                    if sw1 == 0x90:  # Success status
                        card_id = toHexString(response).replace(' ', '')
                        logging.info(f"Successfully read card ID using direct UID command: {card_id}")
                        return card_id, card_type
                except Exception as e:
                    logging.debug(f"Direct UID command failed: {str(e)}")

                # If direct UID failed, try JCOP 3 specific command
                jcop_cmd = [0x80, 0xCA, 0x9F, 0x7F, 0x00]
                try:
                    response, sw1, sw2 = connection.transmit(jcop_cmd)
                    if sw1 == 0x90:  # Success status
                        card_id = toHexString(response).replace(' ', '')
                        logging.info(f"Successfully read card ID using JCOP command: {card_id}")
                        return card_id, card_type
                except Exception as e:
                    logging.debug(f"JCOP command failed: {str(e)}")

                # If both methods failed, try reading ATR as last resort
                if atr:
                    card_id = toHexString(atr).replace(' ', '')
                    logging.info(f"Using ATR as card ID (fallback): {card_id}")
                    return card_id, card_type

                # If we get here, increment retry counter
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logging.warning(f"Failed to read card, retrying ({retry_count}/{MAX_RETRIES})")
                    
            except Exception as e:
                last_error = str(e)
                logging.error(f"Error reading card (Attempt {retry_count + 1}/{MAX_RETRIES}): {last_error}")
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    continue
                break
        
        # If we get here, all retries failed
        error_msg = f"Failed to read card after {MAX_RETRIES} attempts"
        if last_error:
            error_msg += f": {last_error}"
        logging.error(error_msg)
        return None, "Unknown"

    def show_profile(self):
        """Show profile dialog for editing user information"""
        if not self.current_user:
            return
            
        dialog = ProfileDialog(self.current_user, self)
        if dialog.exec() == QDialog.Accepted:
            self.update_status("Profile updated successfully", "success")
            
    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Resize:
            self.bg_widget.setGeometry(self.rect())
        return super().eventFilter(obj, event)

class ProfileDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.parent = parent
        self.setWindowTitle("Edit Profile")
        self.setup_ui()
        self.load_user_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Username (read-only)
        self.username_label = QLineEdit(self.username)
        self.username_label.setReadOnly(True)
        form_layout.addRow("Username:", self.username_label)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        form_layout.addRow("Email:", self.email_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone:", self.phone_input)
        
        # New Password
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("Leave blank to keep current password")
        form_layout.addRow("New Password:", self.new_password_input)
        
        # Confirm New Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Current Password (required for any changes)
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setPlaceholderText("Required to save changes")
        form_layout.addRow("Current Password:", self.current_password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                min-width: 400px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:read-only {
                background-color: #f0f0f0;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton[text="Save Changes"] {
                background-color: #2196F3;
                color: white;
            }
            QPushButton[text="Save Changes"]:hover {
                background-color: #1976D2;
            }
            QPushButton[text="Cancel"] {
                background-color: #f44336;
                color: white;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #d32f2f;
            }
        """)
        
    def load_user_data(self):
        """Load current user data"""
        conn, cursor = self.parent.get_db_connection()
        try:
            cursor.execute('''
                SELECT email, phone 
                FROM users 
                WHERE lower(username) = lower(%s)
            ''', (self.username,))
            result = cursor.fetchone()
            if result:
                email, phone = result
                # Display data exactly as stored
                self.email_input.setText(email if email else "")
                self.phone_input.setText(phone if phone else "")
        finally:
            conn.close()
            
    def save_changes(self):
        """Save profile changes"""
        if not self.current_password_input.text():
            QMessageBox.warning(self, "Error", "Please enter your current password")
            return
            
        # Verify current password
        conn, cursor = self.parent.get_db_connection()
        try:
            cursor.execute('SELECT password_hash FROM users WHERE lower(username) = lower(%s)', 
                         (self.username,))
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "Current password is incorrect")
                return
            stored_hash = result[0]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            if not bcrypt.checkpw(self.current_password_input.text().encode('utf-8'), stored_hash):
                QMessageBox.warning(self, "Error", "Current password is incorrect")
                return
                
            # Verify new passwords match if provided
            new_password = self.new_password_input.text()
            if new_password:
                if new_password != self.confirm_password_input.text():
                    QMessageBox.warning(self, "Error", "New passwords do not match")
                    return
                password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            else:
                password_hash = stored_hash  # Keep existing password
                
            # Update user information preserving exact case
            cursor.execute('''
                UPDATE users 
                SET email = %s, 
                    phone = %s, 
                    password_hash = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE lower(username) = lower(%s)
            ''', (
                self.email_input.text(),  # Store email exactly as entered
                self.phone_input.text(),  # Store phone exactly as entered
                password_hash.decode('utf-8') if isinstance(password_hash, bytes) else password_hash,
                self.username
            ))
            conn.commit()
            self.accept()
            
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to update profile: {str(e)}")
        finally:
            conn.close()

    def showEvent(self, event):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        super().showEvent(event)

class GlassPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet('background: transparent;')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.setBrush(QColor(255, 255, 255, 80))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 32, 32)
        super().paintEvent(event)

# Restore the original entry point for NFCCardManager
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NFCCardManager()
    window.show()
    # Set up timer for card reading
    timer = QTimer()
    timer.timeout.connect(window.check_for_card)
    timer.start(1000)  # Check for card every second
    sys.exit(app.exec_())

# Comment out the MyMontyMainWindow entry point
# if __name__ == '__main__':
#     app = QApplication([])
#     window = MyMontyMainWindow()
#     window.show()
#     app.exec() 