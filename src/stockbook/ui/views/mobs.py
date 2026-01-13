"""Mobs management view for Outback Stockbook."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QComboBox,
    QLabel,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDialogButtonBox,
    QGroupBox,
    QFrame,
)
from PySide6.QtCore import Qt

from stockbook.models.database import Database
from stockbook.models.entities import Mob, Species
from stockbook.ui.views.base import BaseView


class MobDialog(QDialog):
    """Dialog for adding/editing a mob."""

    def __init__(self, db: Database, mob: Mob = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.mob = mob or Mob()
        self.is_new = mob is None

        self.setWindowTitle("Add Mob" if self.is_new else "Edit Mob")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Breeders 2026, Weaners Paddock 5")
        form.addRow("Name:", self.name_edit)

        self.species_combo = QComboBox()
        self.species_combo.addItem("Cattle", Species.CATTLE)
        self.species_combo.addItem("Sheep", Species.SHEEP)
        form.addRow("Species:", self.species_combo)

        self.paddock_combo = QComboBox()
        self.paddock_combo.addItem("(No paddock assigned)", None)
        for paddock in self.db.get_all_paddocks():
            self.paddock_combo.addItem(paddock.name, paddock.id)
        form.addRow("Current Paddock:", self.paddock_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Description or notes about this mob...")
        form.addRow("Description:", self.description_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_fields(self) -> None:
        if not self.is_new:
            self.name_edit.setText(self.mob.name)
            self.description_edit.setPlainText(self.mob.description)

            index = self.species_combo.findData(self.mob.species)
            if index >= 0:
                self.species_combo.setCurrentIndex(index)

            if self.mob.current_paddock_id:
                index = self.paddock_combo.findData(self.mob.current_paddock_id)
                if index >= 0:
                    self.paddock_combo.setCurrentIndex(index)

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a mob name.")
            return

        self.mob.name = name
        self.mob.species = self.species_combo.currentData()
        self.mob.current_paddock_id = self.paddock_combo.currentData()
        self.mob.description = self.description_edit.toPlainText().strip()

        try:
            self.db.save_mob(self.mob)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mob: {e}")


class MobsView(BaseView):
    """View for managing mobs (animal groups)."""

    def __init__(self, db: Database):
        super().__init__(db, "Mobs")
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Action bar
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 10)

        add_btn = QPushButton("Add Mob")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self._on_add_mob)
        action_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._on_edit_mob)
        action_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._on_delete_mob)
        action_layout.addWidget(delete_btn)

        action_layout.addStretch()

        self.main_layout.addWidget(action_bar)

        # Mobs table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Species", "Head Count", "Current Paddock"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_edit_mob)
        self.main_layout.addWidget(self.table)

        # Quick actions
        quick_bar = QWidget()
        quick_bar.setObjectName("quickActionBar")
        quick_layout = QHBoxLayout(quick_bar)

        quick_layout.addWidget(QLabel("Quick Actions:"))

        move_btn = QPushButton("Move Mob to Paddock")
        move_btn.clicked.connect(self._on_move_mob)
        quick_layout.addWidget(move_btn)

        quick_layout.addStretch()

        self.main_layout.addWidget(quick_bar)

    def refresh(self) -> None:
        """Refresh the mobs list."""
        mobs = self.db.get_all_mobs()
        paddocks = {p.id: p.name for p in self.db.get_all_paddocks()}

        self.table.setRowCount(0)

        for mob in mobs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(mob.id)))
            self.table.setItem(row, 1, QTableWidgetItem(mob.name))
            self.table.setItem(row, 2, QTableWidgetItem(mob.species.value.title()))

            count = self.db.get_mob_animal_count(mob.id)
            self.table.setItem(row, 3, QTableWidgetItem(str(count)))

            paddock_name = paddocks.get(mob.current_paddock_id, "")
            self.table.setItem(row, 4, QTableWidgetItem(paddock_name))

    def _get_selected_mob_id(self) -> int | None:
        for item in self.table.selectedItems():
            if item.column() == 0:
                return int(item.text())
        return None

    def _on_add_mob(self) -> None:
        dialog = MobDialog(self.db, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_edit_mob(self) -> None:
        mob_id = self._get_selected_mob_id()
        if not mob_id:
            QMessageBox.information(self, "No Selection", "Please select a mob to edit.")
            return

        mob = self.db.get_mob(mob_id)
        if mob:
            dialog = MobDialog(self.db, mob=mob, parent=self)
            if dialog.exec():
                self.refresh()

    def _on_delete_mob(self) -> None:
        mob_id = self._get_selected_mob_id()
        if not mob_id:
            QMessageBox.information(self, "No Selection", "Please select a mob to delete.")
            return

        mob = self.db.get_mob(mob_id)
        count = self.db.get_mob_animal_count(mob_id) if mob else 0

        msg = f"Are you sure you want to delete mob '{mob.name}'?"
        if count > 0:
            msg += f"\n\n{count} animals are assigned to this mob. They will be unassigned."

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Unassign animals from mob
            for animal in self.db.get_animals_by_mob(mob_id):
                animal.mob_id = None
                self.db.save_animal(animal)
            self.db.delete_mob(mob_id)
            self.refresh()

    def _on_move_mob(self) -> None:
        mob_id = self._get_selected_mob_id()
        if not mob_id:
            QMessageBox.information(self, "No Selection", "Please select a mob to move.")
            return

        mob = self.db.get_mob(mob_id)
        if not mob:
            return

        # Simple paddock selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Move {mob.name} to Paddock")
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        paddock_combo = QComboBox()
        paddock_combo.addItem("(No paddock)", None)
        for paddock in self.db.get_all_paddocks():
            paddock_combo.addItem(paddock.name, paddock.id)

        if mob.current_paddock_id:
            index = paddock_combo.findData(mob.current_paddock_id)
            if index >= 0:
                paddock_combo.setCurrentIndex(index)

        form.addRow("Target Paddock:", paddock_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            mob.current_paddock_id = paddock_combo.currentData()
            self.db.save_mob(mob)
            self.refresh()
