"""Settings view for Outback Stockbook."""

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QFileDialog,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt

from stockbook.models.database import Database
from stockbook.models.entities import PropertySettings
from stockbook.ui.views.base import BaseView


class SettingsView(BaseView):
    """View for application settings and backup/restore."""

    def __init__(self, db: Database):
        super().__init__(db, "Settings")
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Property Settings
        property_group = self._create_property_group()
        content_layout.addWidget(property_group)

        # Backup & Restore
        backup_group = self._create_backup_group()
        content_layout.addWidget(backup_group)

        # Database Info
        db_info_group = self._create_db_info_group()
        content_layout.addWidget(db_info_group)

        content_layout.addStretch()

        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def _create_property_group(self) -> QGroupBox:
        """Create the property settings group."""
        group = QGroupBox("Property Information")
        layout = QFormLayout(group)

        self.property_name_edit = QLineEdit()
        self.property_name_edit.setPlaceholderText("Your property name")
        layout.addRow("Property Name:", self.property_name_edit)

        self.pic_edit = QLineEdit()
        self.pic_edit.setPlaceholderText("Property Identification Code")
        layout.addRow("PIC:", self.pic_edit)

        self.owner_name_edit = QLineEdit()
        self.owner_name_edit.setPlaceholderText("Owner/manager name")
        layout.addRow("Owner Name:", self.owner_name_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Property address")
        layout.addRow("Address:", self.address_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Contact phone")
        layout.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Contact email")
        layout.addRow("Email:", self.email_edit)

        # Save button
        save_btn = QPushButton("Save Property Settings")
        save_btn.setObjectName("actionButton")
        save_btn.clicked.connect(self._save_property_settings)
        layout.addRow("", save_btn)

        return group

    def _create_backup_group(self) -> QGroupBox:
        """Create the backup and restore group."""
        group = QGroupBox("Backup & Restore")
        layout = QVBoxLayout(group)

        # Backup section
        backup_info = QLabel(
            "Regular backups protect your data. We recommend backing up weekly "
            "and before any major changes."
        )
        backup_info.setWordWrap(True)
        backup_info.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(backup_info)

        backup_row = QHBoxLayout()

        backup_btn = QPushButton("Create Backup")
        backup_btn.setObjectName("actionButton")
        backup_btn.clicked.connect(self._create_backup)
        backup_row.addWidget(backup_btn)

        restore_btn = QPushButton("Restore from Backup")
        restore_btn.clicked.connect(self._restore_backup)
        backup_row.addWidget(restore_btn)

        backup_row.addStretch()

        layout.addLayout(backup_row)

        # Last backup info
        self.last_backup_label = QLabel("Last backup: Never")
        self.last_backup_label.setStyleSheet("color: #7f8c8d; margin-top: 10px;")
        layout.addWidget(self.last_backup_label)

        return group

    def _create_db_info_group(self) -> QGroupBox:
        """Create the database info group."""
        group = QGroupBox("Database Information")
        layout = QFormLayout(group)

        self.db_path_label = QLabel()
        self.db_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addRow("Database Location:", self.db_path_label)

        self.db_size_label = QLabel()
        layout.addRow("Database Size:", self.db_size_label)

        self.animal_count_label = QLabel()
        layout.addRow("Total Animals:", self.animal_count_label)

        self.event_count_label = QLabel()
        layout.addRow("Total Events:", self.event_count_label)

        return group

    def refresh(self) -> None:
        """Refresh settings view."""
        self._load_property_settings()
        self._update_db_info()

    def _load_property_settings(self) -> None:
        """Load property settings from database."""
        settings = self.db.get_property_settings()

        if settings:
            self.property_name_edit.setText(settings.property_name)
            self.pic_edit.setText(settings.pic)
            self.owner_name_edit.setText(settings.owner_name)
            self.address_edit.setText(settings.address)
            self.phone_edit.setText(settings.phone)
            self.email_edit.setText(settings.email)

    def _save_property_settings(self) -> None:
        """Save property settings to database."""
        settings = self.db.get_property_settings() or PropertySettings()

        settings.property_name = self.property_name_edit.text().strip()
        settings.pic = self.pic_edit.text().strip()
        settings.owner_name = self.owner_name_edit.text().strip()
        settings.address = self.address_edit.text().strip()
        settings.phone = self.phone_edit.text().strip()
        settings.email = self.email_edit.text().strip()

        try:
            self.db.save_property_settings(settings)
            QMessageBox.information(self, "Saved", "Property settings saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _update_db_info(self) -> None:
        """Update database information display."""
        # Database path
        self.db_path_label.setText(str(self.db.db_path))

        # Database size
        if self.db.db_path.exists():
            size_bytes = self.db.db_path.stat().st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            self.db_size_label.setText(size_str)
        else:
            self.db_size_label.setText("N/A")

        # Animal count
        counts = self.db.get_animal_counts()
        total = sum(counts.values())
        self.animal_count_label.setText(str(total))

        # Event count (approximate from recent events)
        events = self.db.get_recent_events(limit=10000)
        self.event_count_label.setText(str(len(events)))

    def _create_backup(self) -> None:
        """Create a backup of the database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"stockbook_backup_{timestamp}.db"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup",
            str(Path.home() / default_name),
            "Database Files (*.db)",
        )

        if file_path:
            try:
                self.db.backup(Path(file_path))
                self.last_backup_label.setText(
                    f"Last backup: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                )
                QMessageBox.information(
                    self,
                    "Backup Created",
                    f"Database backup saved to:\n{file_path}",
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create backup:\n{e}")

    def _restore_backup(self) -> None:
        """Restore database from a backup."""
        reply = QMessageBox.warning(
            self,
            "Confirm Restore",
            "Restoring from a backup will REPLACE all current data.\n\n"
            "It is recommended to create a backup of your current data first.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            str(Path.home()),
            "Database Files (*.db)",
        )

        if file_path:
            try:
                self.db.restore(Path(file_path))
                QMessageBox.information(
                    self,
                    "Restore Complete",
                    "Database restored successfully.\n\n"
                    "The application data has been updated.",
                )
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore backup:\n{e}")
