"""Quick action dialogs for common operations."""

from datetime import date, timedelta
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QDateEdit,
    QDoubleSpinBox,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
    QGroupBox,
)
from PySide6.QtCore import QDate

from stockbook.models.database import Database
from stockbook.models.entities import (
    Animal,
    AnimalStatus,
    Event,
    MovementEvent,
    TreatmentEvent,
    WeighEvent,
    TreatmentRoute,
)


class QuickMoveDialog(QDialog):
    """Dialog for quickly moving animals to a different mob."""

    def __init__(self, db: Database, animal_ids: list[int], parent=None):
        super().__init__(parent)
        self.db = db
        self.animal_ids = animal_ids

        self.setWindowTitle("Move Animals to Mob")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(f"Moving {len(self.animal_ids)} animal(s) to a new mob")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)

        form = QFormLayout()

        self.mob_combo = QComboBox()
        self.mob_combo.addItem("(Remove from mob)", None)
        for mob in self.db.get_all_mobs():
            self.mob_combo.addItem(mob.name, mob.id)
        form.addRow("Target Mob:", self.mob_combo)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        mob_id = self.mob_combo.currentData()

        for animal_id in self.animal_ids:
            animal = self.db.get_animal(animal_id)
            if animal:
                animal.mob_id = mob_id
                self.db.save_animal(animal)

        self.accept()


class QuickTreatmentDialog(QDialog):
    """Dialog for quickly recording treatments."""

    def __init__(self, db: Database, animal_ids: list[int], parent=None):
        super().__init__(parent)
        self.db = db
        self.animal_ids = animal_ids

        self.setWindowTitle("Record Treatment")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(f"Recording treatment for {len(self.animal_ids)} animal(s)")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)

        # Treatment details
        group = QGroupBox("Treatment Details")
        form = QFormLayout(group)

        self.product_combo = QComboBox()
        self.product_combo.addItem("(Select product)", None)
        for product in self.db.get_all_products():
            self.product_combo.addItem(f"{product.name} ({product.category})", product.id)
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        form.addRow("Product:", self.product_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date:", self.date_edit)

        self.dose_edit = QLineEdit()
        self.dose_edit.setPlaceholderText("e.g., 1ml/10kg")
        form.addRow("Dose:", self.dose_edit)

        self.route_combo = QComboBox()
        for route in TreatmentRoute:
            self.route_combo.addItem(route.value.replace("_", " ").title(), route)
        form.addRow("Route:", self.route_combo)

        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("Batch/lot number")
        form.addRow("Batch No:", self.batch_edit)

        self.admin_edit = QLineEdit()
        self.admin_edit.setPlaceholderText("Who administered")
        form.addRow("Administered By:", self.admin_edit)

        layout.addWidget(group)

        # WHP info
        self.whp_label = QLabel("")
        self.whp_label.setStyleSheet("color: #000000; font-weight: bold;")
        layout.addWidget(self.whp_label)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notes...")
        layout.addWidget(self.notes_edit)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_product_changed(self) -> None:
        product_id = self.product_combo.currentData()
        if product_id:
            product = self.db.get_product(product_id)
            if product:
                self.dose_edit.setText(product.default_dose)
                index = self.route_combo.findData(product.default_route)
                if index >= 0:
                    self.route_combo.setCurrentIndex(index)

                # Show WHP info
                whp_info = []
                if product.meat_whp_days > 0:
                    whp_info.append(f"Meat WHP: {product.meat_whp_days} days")
                if product.milk_whp_days > 0:
                    whp_info.append(f"Milk WHP: {product.milk_whp_days} days")
                if product.esi_days > 0:
                    whp_info.append(f"ESI: {product.esi_days} days")
                self.whp_label.setText(" | ".join(whp_info) if whp_info else "No WHP")

    def _on_accept(self) -> None:
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Validation Error", "Please select a product.")
            return

        product = self.db.get_product(product_id)
        qdate = self.date_edit.date()
        event_date = date(qdate.year(), qdate.month(), qdate.day())

        # Calculate WHP end dates
        meat_whp_end = None
        milk_whp_end = None
        esi_end = None

        if product:
            if product.meat_whp_days > 0:
                meat_whp_end = event_date + timedelta(days=product.meat_whp_days)
            if product.milk_whp_days > 0:
                milk_whp_end = event_date + timedelta(days=product.milk_whp_days)
            if product.esi_days > 0:
                esi_end = event_date + timedelta(days=product.esi_days)

        # Record treatment for each animal
        for animal_id in self.animal_ids:
            event = Event(
                event_date=event_date,
                animal_id=animal_id,
                notes=self.notes_edit.toPlainText().strip(),
                recorded_by=self.admin_edit.text().strip(),
            )

            treatment = TreatmentEvent(
                product_id=product_id,
                batch_number=self.batch_edit.text().strip(),
                dose=self.dose_edit.text().strip(),
                route=self.route_combo.currentData(),
                administered_by=self.admin_edit.text().strip(),
                meat_whp_end=meat_whp_end,
                milk_whp_end=milk_whp_end,
                esi_end=esi_end,
            )

            self.db.save_treatment_event(event, treatment)

        self.accept()


class QuickWeighDialog(QDialog):
    """Dialog for quickly recording weights."""

    def __init__(self, db: Database, animal_ids: list[int], parent=None):
        super().__init__(parent)
        self.db = db
        self.animal_ids = animal_ids

        self.setWindowTitle("Record Weight")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        count = len(self.animal_ids)
        if count == 1:
            animal = self.db.get_animal(self.animal_ids[0])
            info_text = f"Recording weight for: {animal.display_id if animal else 'Unknown'}"
        else:
            info_text = f"Recording weight for {count} animals (will apply same weight to all)"

        info = QLabel(info_text)
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date:", self.date_edit)

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0, 2000)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setDecimals(1)
        form.addRow("Weight:", self.weight_spin)

        self.condition_spin = QDoubleSpinBox()
        self.condition_spin.setRange(0, 5)
        self.condition_spin.setDecimals(1)
        self.condition_spin.setSpecialValueText("N/A")
        form.addRow("Condition Score:", self.condition_spin)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        weight = self.weight_spin.value()
        if weight <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid weight.")
            return

        qdate = self.date_edit.date()
        event_date = date(qdate.year(), qdate.month(), qdate.day())
        condition = self.condition_spin.value() if self.condition_spin.value() > 0 else None

        for animal_id in self.animal_ids:
            event = Event(event_date=event_date, animal_id=animal_id)
            weigh = WeighEvent(weight_kg=weight, condition_score=condition)
            self.db.save_weigh_event(event, weigh)

        self.accept()


class QuickStatusDialog(QDialog):
    """Dialog for quickly changing animal status."""

    def __init__(self, db: Database, animal_ids: list[int], parent=None):
        super().__init__(parent)
        self.db = db
        self.animal_ids = animal_ids

        self.setWindowTitle("Change Status")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(f"Changing status for {len(self.animal_ids)} animal(s)")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)

        form = QFormLayout()

        self.status_combo = QComboBox()
        self.status_combo.addItem("Alive", AnimalStatus.ALIVE)
        self.status_combo.addItem("Sold", AnimalStatus.SOLD)
        self.status_combo.addItem("Dead", AnimalStatus.DEAD)
        self.status_combo.addItem("Missing", AnimalStatus.MISSING)
        form.addRow("New Status:", self.status_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date:", self.date_edit)

        layout.addLayout(form)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notes (reason for status change)...")
        layout.addWidget(self.notes_edit)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        new_status = self.status_combo.currentData()

        for animal_id in self.animal_ids:
            animal = self.db.get_animal(animal_id)
            if animal:
                animal.status = new_status
                self.db.save_animal(animal)

        self.accept()
