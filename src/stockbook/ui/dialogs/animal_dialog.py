"""Dialog for adding/editing animals."""

from datetime import date
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
)
from PySide6.QtCore import QDate

from stockbook.models.database import Database
from stockbook.models.entities import Animal, AnimalStatus, AnimalSex, Species


class AnimalDialog(QDialog):
    """Dialog for adding or editing an animal."""

    def __init__(
        self,
        db: Database,
        animal: Optional[Animal] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.db = db
        self.animal = animal or Animal()
        self.is_new = animal is None

        self.setWindowTitle("Add Animal" if self.is_new else "Edit Animal")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Identification group
        id_group = QGroupBox("Identification")
        id_layout = QFormLayout(id_group)

        self.visual_tag_edit = QLineEdit()
        self.visual_tag_edit.setPlaceholderText("e.g., A001, Blue-42")
        id_layout.addRow("Visual Tag:", self.visual_tag_edit)

        self.eid_edit = QLineEdit()
        self.eid_edit.setPlaceholderText("NLIS tag number")
        id_layout.addRow("EID (NLIS):", self.eid_edit)

        layout.addWidget(id_group)

        # Details group
        details_group = QGroupBox("Details")
        details_layout = QFormLayout(details_group)

        self.species_combo = QComboBox()
        self.species_combo.addItem("Cattle", Species.CATTLE)
        self.species_combo.addItem("Sheep", Species.SHEEP)
        details_layout.addRow("Species:", self.species_combo)

        self.breed_edit = QLineEdit()
        self.breed_edit.setPlaceholderText("e.g., Angus, Merino")
        details_layout.addRow("Breed:", self.breed_edit)

        self.sex_combo = QComboBox()
        self.sex_combo.addItem("Female", AnimalSex.FEMALE)
        self.sex_combo.addItem("Male", AnimalSex.MALE)
        self.sex_combo.addItem("Steer (castrated male cattle)", AnimalSex.STEER)
        self.sex_combo.addItem("Wether (castrated male sheep)", AnimalSex.WETHER)
        details_layout.addRow("Sex:", self.sex_combo)

        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        self.dob_edit.setDisplayFormat("dd/MM/yyyy")
        details_layout.addRow("Date of Birth:", self.dob_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Alive", AnimalStatus.ALIVE)
        self.status_combo.addItem("Sold", AnimalStatus.SOLD)
        self.status_combo.addItem("Dead", AnimalStatus.DEAD)
        self.status_combo.addItem("Missing", AnimalStatus.MISSING)
        details_layout.addRow("Status:", self.status_combo)

        layout.addWidget(details_group)

        # Mob group
        mob_group = QGroupBox("Mob Assignment")
        mob_layout = QFormLayout(mob_group)

        self.mob_combo = QComboBox()
        self.mob_combo.addItem("(No Mob)", None)
        for mob in self.db.get_all_mobs():
            self.mob_combo.addItem(mob.name, mob.id)
        mob_layout.addRow("Mob:", self.mob_combo)

        layout.addWidget(mob_group)

        # Notes group
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Additional notes about this animal...")
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_fields(self) -> None:
        """Populate fields with existing animal data."""
        if not self.is_new:
            self.visual_tag_edit.setText(self.animal.visual_tag)
            self.eid_edit.setText(self.animal.eid)
            self.breed_edit.setText(self.animal.breed)
            self.notes_edit.setPlainText(self.animal.notes)

            # Set combo box selections
            index = self.species_combo.findData(self.animal.species)
            if index >= 0:
                self.species_combo.setCurrentIndex(index)

            index = self.sex_combo.findData(self.animal.sex)
            if index >= 0:
                self.sex_combo.setCurrentIndex(index)

            index = self.status_combo.findData(self.animal.status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

            if self.animal.mob_id:
                index = self.mob_combo.findData(self.animal.mob_id)
                if index >= 0:
                    self.mob_combo.setCurrentIndex(index)

            if self.animal.date_of_birth:
                qdate = QDate(
                    self.animal.date_of_birth.year,
                    self.animal.date_of_birth.month,
                    self.animal.date_of_birth.day,
                )
                self.dob_edit.setDate(qdate)

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate
        visual_tag = self.visual_tag_edit.text().strip()
        eid = self.eid_edit.text().strip()

        if not visual_tag and not eid:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter at least a Visual Tag or EID.",
            )
            return

        # Update animal object
        self.animal.visual_tag = visual_tag
        self.animal.eid = eid
        self.animal.species = self.species_combo.currentData()
        self.animal.breed = self.breed_edit.text().strip()
        self.animal.sex = self.sex_combo.currentData()
        self.animal.status = self.status_combo.currentData()
        self.animal.mob_id = self.mob_combo.currentData()
        self.animal.notes = self.notes_edit.toPlainText().strip()

        qdate = self.dob_edit.date()
        self.animal.date_of_birth = date(qdate.year(), qdate.month(), qdate.day())

        # Save to database
        try:
            self.db.save_animal(self.animal)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save animal: {e}")
