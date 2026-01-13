"""Base view class for all views."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt

from stockbook.models.database import Database


class BaseView(QWidget):
    """Base class for all main views."""

    def __init__(self, db: Database, title: str = ""):
        super().__init__()
        self.db = db
        self._title = title

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

    def refresh(self) -> None:
        """Refresh the view data. Override in subclasses."""
        pass

    def create_header(self, title: str, subtitle: str = "") -> QWidget:
        """Create a standard header widget."""
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 10)

        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("subtitleLabel")
            layout.addWidget(subtitle_label)

        return header

    def create_action_bar(self, actions: list[tuple[str, callable, str]]) -> QWidget:
        """Create a horizontal action bar with buttons.

        Args:
            actions: List of (label, callback, style) tuples.
                    style can be 'primary', 'success', 'danger', or 'default'
        """
        bar = QWidget()
        bar.setObjectName("quickActionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 10, 0, 10)

        for label, callback, style in actions:
            btn = QPushButton(label)

            if style == "success":
                btn.setObjectName("actionButton")
            elif style == "danger":
                btn.setObjectName("dangerButton")

            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()
        return bar
