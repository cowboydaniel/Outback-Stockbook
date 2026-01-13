"""Treatments view for Outback Stockbook."""

from datetime import date, timedelta

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
    QSpinBox,
    QComboBox,
    QDialogButtonBox,
    QTabWidget,
    QFrame,
    QGroupBox,
)
from PySide6.QtCore import Qt

from stockbook.models.database import Database
from stockbook.models.entities import Product, TreatmentRoute, EventType
from stockbook.ui.views.base import BaseView


class ProductDialog(QDialog):
    """Dialog for adding/editing treatment products."""

    def __init__(self, db: Database, product: Product = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.product = product or Product()
        self.is_new = product is None

        self.setWindowTitle("Add Product" if self.is_new else "Edit Product")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Basic info
        basic_group = QGroupBox("Product Information")
        basic_form = QFormLayout(basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Dectomax, Cydectin, 7in1")
        basic_form.addRow("Name:", self.name_edit)

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems([
            "Drench",
            "Vaccine",
            "Antibiotic",
            "Anti-inflammatory",
            "Vitamin/Mineral",
            "Hormone",
            "Pour-On",
            "Other",
        ])
        basic_form.addRow("Category:", self.category_combo)

        self.ingredient_edit = QLineEdit()
        self.ingredient_edit.setPlaceholderText("Active ingredient")
        basic_form.addRow("Active Ingredient:", self.ingredient_edit)

        self.route_combo = QComboBox()
        for route in TreatmentRoute:
            self.route_combo.addItem(route.value.replace("_", " ").title(), route)
        basic_form.addRow("Default Route:", self.route_combo)

        self.dose_edit = QLineEdit()
        self.dose_edit.setPlaceholderText("e.g., 1ml/10kg, 2ml/head")
        basic_form.addRow("Default Dose:", self.dose_edit)

        layout.addWidget(basic_group)

        # Withholding periods
        whp_group = QGroupBox("Withholding Periods (days)")
        whp_form = QFormLayout(whp_group)

        self.meat_whp_spin = QSpinBox()
        self.meat_whp_spin.setRange(0, 365)
        self.meat_whp_spin.setSuffix(" days")
        whp_form.addRow("Meat WHP:", self.meat_whp_spin)

        self.milk_whp_spin = QSpinBox()
        self.milk_whp_spin.setRange(0, 365)
        self.milk_whp_spin.setSuffix(" days")
        whp_form.addRow("Milk WHP:", self.milk_whp_spin)

        self.esi_spin = QSpinBox()
        self.esi_spin.setRange(0, 365)
        self.esi_spin.setSuffix(" days")
        whp_form.addRow("Export Slaughter Interval:", self.esi_spin)

        layout.addWidget(whp_group)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Additional notes...")
        layout.addWidget(self.notes_edit)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_fields(self) -> None:
        if not self.is_new:
            self.name_edit.setText(self.product.name)
            self.category_combo.setCurrentText(self.product.category)
            self.ingredient_edit.setText(self.product.active_ingredient)
            self.dose_edit.setText(self.product.default_dose)
            self.notes_edit.setPlainText(self.product.notes)

            self.meat_whp_spin.setValue(self.product.meat_whp_days)
            self.milk_whp_spin.setValue(self.product.milk_whp_days)
            self.esi_spin.setValue(self.product.esi_days)

            index = self.route_combo.findData(self.product.default_route)
            if index >= 0:
                self.route_combo.setCurrentIndex(index)

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a product name.")
            return

        self.product.name = name
        self.product.category = self.category_combo.currentText()
        self.product.active_ingredient = self.ingredient_edit.text().strip()
        self.product.default_dose = self.dose_edit.text().strip()
        self.product.default_route = self.route_combo.currentData()
        self.product.meat_whp_days = self.meat_whp_spin.value()
        self.product.milk_whp_days = self.milk_whp_spin.value()
        self.product.esi_days = self.esi_spin.value()
        self.product.notes = self.notes_edit.toPlainText().strip()

        try:
            self.db.save_product(self.product)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save product: {e}")


class TreatmentsView(BaseView):
    """View for managing treatments and withholding periods."""

    def __init__(self, db: Database):
        super().__init__(db, "Treatments")
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Tabs for different views
        tabs = QTabWidget()

        # WHP Dashboard tab
        whp_tab = self._create_whp_tab()
        tabs.addTab(whp_tab, "WHP Dashboard")

        # Treatment History tab
        history_tab = self._create_history_tab()
        tabs.addTab(history_tab, "Treatment History")

        # Products tab
        products_tab = self._create_products_tab()
        tabs.addTab(products_tab, "Products")

        self.main_layout.addWidget(tabs)

    def _create_whp_tab(self) -> QWidget:
        """Create the WHP (Withholding Period) dashboard tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel("Animals Currently on Withholding Period")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(header)

        info = QLabel(
            "These animals must not be sold for slaughter until their withholding period ends."
        )
        info.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info)

        # WHP table
        self.whp_table = QTableWidget()
        self.whp_table.setColumnCount(6)
        self.whp_table.setHorizontalHeaderLabels([
            "Tag", "Product", "Treatment Date", "Meat WHP End", "Milk WHP End", "Days Until Clear"
        ])
        self.whp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.whp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.whp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.whp_table.setAlternatingRowColors(True)
        layout.addWidget(self.whp_table)

        # Empty state
        self.whp_empty = QLabel("No animals currently on withholding period - all clear!")
        self.whp_empty.setStyleSheet(
            "color: #27ae60; font-size: 16px; font-style: italic; padding: 40px;"
        )
        self.whp_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.whp_empty.hide()
        layout.addWidget(self.whp_empty)

        return tab

    def _create_history_tab(self) -> QWidget:
        """Create the treatment history tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel("Recent Treatments")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Animal/Mob", "Product", "Dose", "Route", "Administered By"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)

        return tab

    def _create_products_tab(self) -> QWidget:
        """Create the products management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Action bar
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 10)

        add_btn = QPushButton("Add Product")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self._on_add_product)
        action_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._on_edit_product)
        action_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._on_delete_product)
        action_layout.addWidget(delete_btn)

        action_layout.addStretch()

        layout.addWidget(action_bar)

        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Name", "Category", "Meat WHP", "Milk WHP", "ESI"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.doubleClicked.connect(self._on_edit_product)
        layout.addWidget(self.products_table)

        return tab

    def refresh(self) -> None:
        """Refresh all treatment data."""
        self._refresh_whp()
        self._refresh_history()
        self._refresh_products()

    def _refresh_whp(self) -> None:
        """Refresh the WHP dashboard."""
        whp_animals = self.db.get_animals_on_whp()

        self.whp_table.setRowCount(0)

        if not whp_animals:
            self.whp_table.hide()
            self.whp_empty.show()
            return

        self.whp_table.show()
        self.whp_empty.hide()

        today = date.today()

        for item in whp_animals:
            row = self.whp_table.rowCount()
            self.whp_table.insertRow(row)

            tag = item["visual_tag"] or item["eid"] or f"#{item['animal_id']}"
            self.whp_table.setItem(row, 0, QTableWidgetItem(tag))
            self.whp_table.setItem(row, 1, QTableWidgetItem(item["product_name"] or "Unknown"))
            self.whp_table.setItem(row, 2, QTableWidgetItem(str(item["event_date"])))

            meat_end = item["meat_whp_end"]
            milk_end = item["milk_whp_end"]

            self.whp_table.setItem(row, 3, QTableWidgetItem(str(meat_end) if meat_end else "N/A"))
            self.whp_table.setItem(row, 4, QTableWidgetItem(str(milk_end) if milk_end else "N/A"))

            # Calculate days until clear (use meat WHP as primary)
            if meat_end:
                days_left = (meat_end - today).days
                days_item = QTableWidgetItem(str(days_left))
                if days_left <= 3:
                    days_item.setBackground(Qt.GlobalColor.red)
                    days_item.setForeground(Qt.GlobalColor.white)
                elif days_left <= 7:
                    days_item.setBackground(Qt.GlobalColor.yellow)
                self.whp_table.setItem(row, 5, days_item)
            else:
                self.whp_table.setItem(row, 5, QTableWidgetItem("-"))

    def _refresh_history(self) -> None:
        """Refresh the treatment history."""
        # Get recent treatment events
        from stockbook.models.entities import EventType

        self.history_table.setRowCount(0)

        events = self.db.get_recent_events(limit=100)
        treatment_events = [e for e in events if e.event_type == EventType.TREATMENT]

        products = {p.id: p.name for p in self.db.get_all_products()}

        for event in treatment_events[:50]:
            treatment = self.db.get_treatment_details(event.id)
            if not treatment:
                continue

            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            self.history_table.setItem(row, 0, QTableWidgetItem(str(event.event_date)))

            # Get animal/mob identifier
            identifier = ""
            if event.animal_id:
                animal = self.db.get_animal(event.animal_id)
                if animal:
                    identifier = animal.display_id
            elif event.mob_id:
                mob = self.db.get_mob(event.mob_id)
                if mob:
                    identifier = f"Mob: {mob.name}"

            self.history_table.setItem(row, 1, QTableWidgetItem(identifier))
            self.history_table.setItem(
                row, 2, QTableWidgetItem(products.get(treatment.product_id, "Unknown"))
            )
            self.history_table.setItem(row, 3, QTableWidgetItem(treatment.dose))
            self.history_table.setItem(
                row, 4, QTableWidgetItem(treatment.route.value.replace("_", " ").title())
            )
            self.history_table.setItem(row, 5, QTableWidgetItem(treatment.administered_by))

    def _refresh_products(self) -> None:
        """Refresh the products list."""
        products = self.db.get_all_products()

        self.products_table.setRowCount(0)

        for product in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)

            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.category))
            self.products_table.setItem(
                row, 3, QTableWidgetItem(f"{product.meat_whp_days} days")
            )
            self.products_table.setItem(
                row, 4, QTableWidgetItem(f"{product.milk_whp_days} days")
            )
            self.products_table.setItem(row, 5, QTableWidgetItem(f"{product.esi_days} days"))

    def _get_selected_product_id(self) -> int | None:
        for item in self.products_table.selectedItems():
            if item.column() == 0:
                return int(item.text())
        return None

    def _on_add_product(self) -> None:
        dialog = ProductDialog(self.db, parent=self)
        if dialog.exec():
            self.refresh()

    def _on_edit_product(self) -> None:
        product_id = self._get_selected_product_id()
        if not product_id:
            QMessageBox.information(self, "No Selection", "Please select a product to edit.")
            return

        product = self.db.get_product(product_id)
        if product:
            dialog = ProductDialog(self.db, product=product, parent=self)
            if dialog.exec():
                self.refresh()

    def _on_delete_product(self) -> None:
        product_id = self._get_selected_product_id()
        if not product_id:
            QMessageBox.information(self, "No Selection", "Please select a product to delete.")
            return

        product = self.db.get_product(product_id)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete product '{product.name}'?\n\n"
            "This will not delete treatment records that used this product.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_product(product_id)
            self.refresh()
