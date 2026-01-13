"""Paddocks management view for Outback Stockbook."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDoubleSpinBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt

from stockbook.models.database import Database
from stockbook.models.entities import Paddock
from stockbook.ui.views.base import BaseView


class PaddockDialog(QDialog):
    """Dialog for adding/editing a paddock."""

    def __init__(self, db: Database, paddock: Paddock = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.paddock = paddock or Paddock()
        self.is_new = paddock is None

        self.setWindowTitle("Add Paddock" if self.is_new else "Edit Paddock")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., North River, House Paddock")
        form.addRow("Name:", self.name_edit)

        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(0, 100000)
        self.area_spin.setSuffix(" ha")
        self.area_spin.setDecimals(1)
        self.area_spin.setSpecialValueText("Unknown")
        form.addRow("Area:", self.area_spin)

        self.pic_edit = QLineEdit()
        self.pic_edit.setPlaceholderText("Property Identification Code (if different)")
        form.addRow("PIC:", self.pic_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Notes about this paddock (water, fencing, etc.)...")
        form.addRow("Notes:", self.notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_fields(self) -> None:
        if not self.is_new:
            self.name_edit.setText(self.paddock.name)
            self.pic_edit.setText(self.paddock.pic)
            self.notes_edit.setPlainText(self.paddock.notes)

            if self.paddock.area_hectares:
                self.area_spin.setValue(self.paddock.area_hectares)

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a paddock name.")
            return

        self.paddock.name = name
        self.paddock.area_hectares = (
            self.area_spin.value() if self.area_spin.value() > 0 else None
        )
        self.paddock.pic = self.pic_edit.text().strip()
        self.paddock.notes = self.notes_edit.toPlainText().strip()

        try:
            self.db.save_paddock(self.paddock)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save paddock: {e}")


class PaddocksView(BaseView):
    """View for managing paddocks."""

    def __init__(self, db: Database):
        super().__init__(db, "Paddocks")
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Action bar
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 10)

        add_btn = QPushButton("Add Paddock")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self._on_add_paddock)
        action_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._on_edit_paddock)
        action_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._on_delete_paddock)
        action_layout.addWidget(delete_btn)

        action_layout.addStretch()

        self.main_layout.addWidget(action_bar)

        # Paddocks table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Area (ha)", "PIC", "Mobs Currently"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_edit_paddock)
        self.main_layout.addWidget(self.table)

    def refresh(self) -> None:
        """Refresh the paddocks list."""
        paddocks = self.db.get_all_paddocks()
        mobs = self.db.get_all_mobs()

        # Build paddock -> mobs mapping
        paddock_mobs: dict[int, list[str]] = {}
        for mob in mobs:
            if mob.current_paddock_id:
                if mob.current_paddock_id not in paddock_mobs:
                    paddock_mobs[mob.current_paddock_id] = []
                paddock_mobs[mob.current_paddock_id].append(mob.name)

        self.table.setRowCount(0)

        for paddock in paddocks:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(paddock.id)))
            self.table.setItem(row, 1, QTableWidgetItem(paddock.name))

            area_str = f"{paddock.area_hectares:.1f}" if paddock.area_hectares else ""
            self.table.setItem(row, 2, QTableWidgetItem(area_str))
            self.table.setItem(row, 3, QTableWidgetItem(paddock.pic))

            mob_names = paddock_mobs.get(paddock.id, [])
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(mob_names)))

    def _get_selected_paddock_id(self) -> int | None:
        for item in self.table.selectedItems():
            if item.column() == 0:
                return int(item.text())
        return None

    def _on_add_paddock(self) -> None:
        dialog = PaddockDialog(self.db, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_edit_paddock(self) -> None:
        paddock_id = self._get_selected_paddock_id()
        if not paddock_id:
            QMessageBox.information(self, "No Selection", "Please select a paddock to edit.")
            return

        paddock = self.db.get_paddock(paddock_id)
        if paddock:
            dialog = PaddockDialog(self.db, paddock=paddock, parent=self)
            if dialog.exec():
                self.refresh()

    def _on_delete_paddock(self) -> None:
        paddock_id = self._get_selected_paddock_id()
        if not paddock_id:
            QMessageBox.information(self, "No Selection", "Please select a paddock to delete.")
            return

        paddock = self.db.get_paddock(paddock_id)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete paddock '{paddock.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Unassign mobs from paddock
            for mob in self.db.get_all_mobs():
                if mob.current_paddock_id == paddock_id:
                    mob.current_paddock_id = None
                    self.db.save_mob(mob)
            self.db.delete_paddock(paddock_id)
            self.refresh()
