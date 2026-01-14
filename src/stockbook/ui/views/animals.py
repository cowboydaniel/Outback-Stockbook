"""Animals management view for Outback Stockbook."""

from datetime import date

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
    QLineEdit,
    QFrame,
)
from PySide6.QtCore import Qt

from stockbook.models.database import Database
from stockbook.models.entities import Animal, AnimalStatus, AnimalSex, Species
from stockbook.ui.views.base import BaseView
from stockbook.ui.dialogs.animal_dialog import AnimalDialog


class AnimalsView(BaseView):
    """View for managing individual animals."""

    def __init__(self, db: Database):
        super().__init__(db, "Animals")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the animals view UI."""
        # Filter bar
        filter_bar = self._create_filter_bar()
        self.main_layout.addWidget(filter_bar)

        # Action bar
        action_bar = self._create_action_bar()
        self.main_layout.addWidget(action_bar)

        # Animals table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Visual Tag", "EID", "Species", "Breed", "Sex", "Mob", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_edit_animal)
        self.main_layout.addWidget(self.table)

        # Quick action bar at bottom
        quick_bar = self._create_quick_action_bar()
        self.main_layout.addWidget(quick_bar)

    def _create_filter_bar(self) -> QWidget:
        """Create the filter bar."""
        bar = QFrame()
        bar.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 4px;")
        layout = QHBoxLayout(bar)

        # Search field
        layout.addWidget(QLabel("Search:"))
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Tag or EID...")
        self.search_field.setMaximumWidth(200)
        self.search_field.textChanged.connect(self._apply_filters)
        layout.addWidget(self.search_field)

        layout.addSpacing(20)

        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", None)
        self.status_filter.addItem("Alive", AnimalStatus.ALIVE)
        self.status_filter.addItem("Sold", AnimalStatus.SOLD)
        self.status_filter.addItem("Dead", AnimalStatus.DEAD)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.status_filter)

        layout.addSpacing(20)

        # Species filter
        layout.addWidget(QLabel("Species:"))
        self.species_filter = QComboBox()
        self.species_filter.addItem("All", None)
        self.species_filter.addItem("Cattle", Species.CATTLE)
        self.species_filter.addItem("Sheep", Species.SHEEP)
        self.species_filter.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.species_filter)

        layout.addSpacing(20)

        # Mob filter
        layout.addWidget(QLabel("Mob:"))
        self.mob_filter = QComboBox()
        self.mob_filter.setMinimumWidth(150)
        self.mob_filter.currentIndexChanged.connect(self._apply_filters)
        layout.addWidget(self.mob_filter)

        layout.addStretch()

        # Count label
        self.count_label = QLabel("0 animals")
        self.count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.count_label)

        return bar

    def _create_action_bar(self) -> QWidget:
        """Create the main action bar."""
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 10, 0, 10)

        add_btn = QPushButton("Add Animal")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self._on_add_animal)
        layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._on_edit_animal)
        layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._on_delete_animal)
        layout.addWidget(delete_btn)

        layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        return bar

    def _create_quick_action_bar(self) -> QWidget:
        """Create the quick action bar at the bottom."""
        bar = QWidget()
        bar.setObjectName("quickActionBar")
        layout = QHBoxLayout(bar)

        layout.addWidget(QLabel("Quick Actions:"))

        move_btn = QPushButton("Move to Mob")
        move_btn.clicked.connect(self._on_quick_move)
        layout.addWidget(move_btn)

        treat_btn = QPushButton("Record Treatment")
        treat_btn.clicked.connect(self._on_quick_treat)
        layout.addWidget(treat_btn)

        weigh_btn = QPushButton("Record Weight")
        weigh_btn.clicked.connect(self._on_quick_weigh)
        layout.addWidget(weigh_btn)

        status_btn = QPushButton("Change Status")
        status_btn.clicked.connect(self._on_quick_status)
        layout.addWidget(status_btn)

        layout.addStretch()

        return bar

    def refresh(self) -> None:
        """Refresh the animals list."""
        self._refresh_mob_filter()
        self._apply_filters()

    def _refresh_mob_filter(self) -> None:
        """Refresh the mob filter dropdown."""
        current = self.mob_filter.currentData()
        self.mob_filter.blockSignals(True)
        self.mob_filter.clear()
        self.mob_filter.addItem("All Mobs", None)

        for mob in self.db.get_all_mobs():
            self.mob_filter.addItem(mob.name, mob.id)

        # Restore selection
        if current:
            index = self.mob_filter.findData(current)
            if index >= 0:
                self.mob_filter.setCurrentIndex(index)

        self.mob_filter.blockSignals(False)

    def _apply_filters(self) -> None:
        """Apply filters and refresh the table."""
        status = self.status_filter.currentData()
        species = self.species_filter.currentData()
        mob_id = self.mob_filter.currentData()
        search_text = self.search_field.text().strip().lower()

        # Get animals
        if status:
            animals = self.db.get_all_animals(status=status)
        else:
            animals = self.db.get_all_animals()

        # Apply additional filters
        filtered = []
        for animal in animals:
            # Species filter
            if species and animal.species != species:
                continue

            # Mob filter
            if mob_id and animal.mob_id != mob_id:
                continue

            # Search filter
            if search_text:
                searchable = (animal.visual_tag + animal.eid + animal.breed).lower()
                if search_text not in searchable:
                    continue

            filtered.append(animal)

        self._populate_table(filtered)

    def _populate_table(self, animals: list[Animal]) -> None:
        """Populate the table with animals."""
        self.table.setRowCount(0)

        # Cache mobs for display
        mobs = {m.id: m.name for m in self.db.get_all_mobs()}

        for animal in animals:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(animal.id)))
            self.table.setItem(row, 1, QTableWidgetItem(animal.visual_tag))
            self.table.setItem(row, 2, QTableWidgetItem(animal.eid))
            self.table.setItem(row, 3, QTableWidgetItem(animal.species.value.title()))
            self.table.setItem(row, 4, QTableWidgetItem(animal.breed))
            self.table.setItem(row, 5, QTableWidgetItem(animal.sex.value.title()))
            self.table.setItem(row, 6, QTableWidgetItem(mobs.get(animal.mob_id, "")))

            status_item = QTableWidgetItem(animal.status.value.title())
            if animal.status == AnimalStatus.DEAD:
                status_item.setBackground(Qt.GlobalColor.black)
                status_item.setForeground(Qt.GlobalColor.white)
            elif animal.status == AnimalStatus.SOLD:
                status_item.setBackground(Qt.GlobalColor.black)
                status_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 7, status_item)

        self.count_label.setText(f"{len(animals)} animals")

    def _get_selected_animal_ids(self) -> list[int]:
        """Get the IDs of selected animals."""
        ids = []
        for item in self.table.selectedItems():
            if item.column() == 0:  # ID column
                ids.append(int(item.text()))
        return ids

    def _on_add_animal(self) -> None:
        """Handle adding a new animal."""
        dialog = AnimalDialog(self.db, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_edit_animal(self) -> None:
        """Handle editing the selected animal."""
        ids = self._get_selected_animal_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Please select an animal to edit.")
            return

        animal = self.db.get_animal(ids[0])
        if animal:
            dialog = AnimalDialog(self.db, animal=animal, parent=self)
            if dialog.exec():
                self.refresh()

    def _on_delete_animal(self) -> None:
        """Handle deleting selected animals."""
        ids = self._get_selected_animal_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Please select animals to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {len(ids)} animal(s)?\n\n"
            "This will also delete all associated events and records.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for animal_id in ids:
                self.db.delete_animal(animal_id)
            self.refresh()

    def _on_quick_move(self) -> None:
        """Handle quick move to mob."""
        ids = self._get_selected_animal_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Please select animals to move.")
            return

        from stockbook.ui.dialogs.quick_actions import QuickMoveDialog

        dialog = QuickMoveDialog(self.db, ids, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_quick_treat(self) -> None:
        """Handle quick treatment recording."""
        ids = self._get_selected_animal_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Please select animals to treat.")
            return

        from stockbook.ui.dialogs.quick_actions import QuickTreatmentDialog

        dialog = QuickTreatmentDialog(self.db, ids, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_quick_weigh(self) -> None:
        """Handle quick weight recording."""
        ids = self._get_selected_animal_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Please select animals to weigh.")
            return

        from stockbook.ui.dialogs.quick_actions import QuickWeighDialog

        dialog = QuickWeighDialog(self.db, ids, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_quick_status(self) -> None:
        """Handle quick status change."""
        ids = self._get_selected_animal_ids()
        if not ids:
            QMessageBox.information(self, "No Selection", "Please select animals to update.")
            return

        from stockbook.ui.dialogs.quick_actions import QuickStatusDialog

        dialog = QuickStatusDialog(self.db, ids, parent=self)
        if dialog.exec():
            self.refresh()

    def search(self, query: str) -> None:
        """Search for animals matching the query."""
        self.search_field.setText(query)
        self._apply_filters()
