"""Main entry point for Outback Stockbook."""

import sys
from pathlib import Path

# Add src directory to path when running directly
_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor

from stockbook import __app_name__, __version__
from stockbook.models.database import Database
from stockbook.ui.main_window import MainWindow


def main():
    """Application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Outback Stockbook")

    # Set a readable default font
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    # Set palette for placeholder text to be black
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#000000"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
    app.setPalette(palette)

    # Apply dark-friendly stylesheet for outdoor visibility
    app.setStyleSheet(get_stylesheet())

    # Initialize database
    db = Database()
    db.connect()

    # Create and show main window
    window = MainWindow(db)
    window.show()

    # Run application
    exit_code = app.exec()

    # Cleanup
    db.close()

    sys.exit(exit_code)


def get_stylesheet() -> str:
    """Return the application stylesheet.

    Designed for visibility in bright outdoor conditions with
    high contrast and large touch-friendly elements.
    """
    return """
        /* Main window */
        QMainWindow {
            background-color: #f5f5f5;
        }

        /* Sidebar navigation */
        #sidebar {
            background-color: #2c3e50;
            min-width: 200px;
            max-width: 200px;
        }

        #sidebar QPushButton {
            background-color: transparent;
            color: #ffffff;
            border: none;
            padding: 15px 20px;
            text-align: left;
            font-size: 14px;
            font-weight: bold;
        }

        #sidebar QPushButton:hover {
            background-color: #34495e;
        }

        #sidebar QPushButton:checked {
            background-color: #3498db;
        }

        /* Content area */
        #content {
            background-color: #ffffff;
        }

        /* Tables - high visibility */
        QTableWidget, QTableView {
            background-color: #ffffff;
            color: #000000;
            alternate-background-color: #f8f9fa;
            gridline-color: #dee2e6;
            font-size: 13px;
            selection-background-color: #3498db;
            selection-color: #ffffff;
        }

        QTableWidget::item, QTableView::item {
            padding: 8px;
            color: #000000;
        }

        QHeaderView::section {
            background-color: #2c3e50;
            color: #ffffff;
            padding: 10px;
            border: none;
            font-weight: bold;
            font-size: 13px;
        }

        /* Buttons - large and touch-friendly */
        QPushButton {
            background-color: #3498db;
            color: #ffffff;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            min-height: 40px;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #1f6dad;
        }

        QPushButton:disabled {
            background-color: #bdc3c7;
        }

        /* Action buttons */
        QPushButton#actionButton {
            background-color: #27ae60;
        }

        QPushButton#actionButton:hover {
            background-color: #229954;
        }

        QPushButton#dangerButton {
            background-color: #e74c3c;
        }

        QPushButton#dangerButton:hover {
            background-color: #c0392b;
        }

        /* Input fields - large and clear */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
        QDateEdit, QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 2px solid #bdc3c7;
            border-radius: 4px;
            padding: 10px;
            font-size: 14px;
            min-height: 40px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {
            border-color: #3498db;
        }

        /* Placeholder text */
        QLineEdit[text=""], QLineEdit:placeholder {
            color: #000000;
        }

        QComboBox::drop-down {
            border: none;
            width: 30px;
        }

        QComboBox::down-arrow {
            width: 12px;
            height: 12px;
        }

        /* Dropdown list items */
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
            selection-background-color: #3498db;
            selection-color: #ffffff;
        }

        /* Labels */
        QLabel {
            font-size: 13px;
            color: #000000;
        }

        QLabel#titleLabel {
            font-size: 24px;
            font-weight: bold;
            color: #000000;
        }

        QLabel#subtitleLabel {
            font-size: 16px;
            color: #000000;
        }

        /* Group boxes */
        QGroupBox {
            font-weight: bold;
            font-size: 14px;
            color: #000000;
            border: 2px solid #bdc3c7;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #000000;
        }

        /* Search bar */
        #searchBar {
            background-color: #ffffff;
            color: #000000;
            border: 2px solid #3498db;
            border-radius: 20px;
            padding: 10px 20px;
            font-size: 14px;
            min-height: 40px;
        }

        /* Status indicators */
        QLabel#warningLabel {
            background-color: #f39c12;
            color: #ffffff;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        }

        QLabel#dangerLabel {
            background-color: #e74c3c;
            color: #ffffff;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        }

        QLabel#successLabel {
            background-color: #27ae60;
            color: #ffffff;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        }

        /* Scroll bars */
        QScrollBar:vertical {
            background: #f5f5f5;
            width: 16px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: #bdc3c7;
            min-height: 40px;
            border-radius: 8px;
        }

        QScrollBar::handle:vertical:hover {
            background: #95a5a6;
        }

        QScrollBar:horizontal {
            background: #f5f5f5;
            height: 16px;
            margin: 0;
        }

        QScrollBar::handle:horizontal {
            background: #bdc3c7;
            min-width: 40px;
            border-radius: 8px;
        }

        /* Tool tips */
        QToolTip {
            background-color: #2c3e50;
            color: #ffffff;
            border: none;
            padding: 8px;
            font-size: 12px;
        }

        /* Tab widget */
        QTabWidget::pane {
            border: 2px solid #bdc3c7;
            border-radius: 4px;
        }

        QTabBar::tab {
            background-color: #ecf0f1;
            color: #000000;
            padding: 12px 24px;
            font-size: 13px;
            font-weight: bold;
        }

        QTabBar::tab:selected {
            background-color: #3498db;
            color: #ffffff;
        }

        QTabBar::tab:hover:!selected {
            background-color: #bdc3c7;
            color: #000000;
        }

        /* Cards / Frames */
        QFrame#card {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
        }

        /* Quick action bar */
        #quickActionBar {
            background-color: #ecf0f1;
            padding: 10px;
            border-top: 2px solid #bdc3c7;
        }

        #quickActionBar QPushButton {
            min-width: 100px;
        }
    """


if __name__ == "__main__":
    main()
