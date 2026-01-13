"""Weights view for Outback Stockbook."""

from datetime import date, timedelta
from typing import Optional

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
    QComboBox,
    QFrame,
    QGroupBox,
    QFormLayout,
    QDateEdit,
)
from PySide6.QtCore import Qt, QDate

from stockbook.models.database import Database
from stockbook.models.entities import EventType
from stockbook.ui.views.base import BaseView


class WeightsView(BaseView):
    """View for managing weight records and growth analysis."""

    def __init__(self, db: Database):
        super().__init__(db, "Weights")
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Filter bar
        filter_bar = self._create_filter_bar()
        self.main_layout.addWidget(filter_bar)

        # Stats summary
        stats_row = self._create_stats_row()
        self.main_layout.addWidget(stats_row)

        # Weights table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Animal", "Weight (kg)", "Condition Score", "ADG (kg/day)", "Notes"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.main_layout.addWidget(self.table)

        # Action bar
        action_bar = QWidget()
        action_bar.setObjectName("quickActionBar")
        action_layout = QHBoxLayout(action_bar)

        record_btn = QPushButton("Record New Weights")
        record_btn.setObjectName("actionButton")
        record_btn.clicked.connect(self._on_record_weights)
        action_layout.addWidget(record_btn)

        action_layout.addStretch()

        self.main_layout.addWidget(action_bar)

    def _create_filter_bar(self) -> QWidget:
        """Create the filter bar."""
        bar = QFrame()
        bar.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 4px;")
        layout = QHBoxLayout(bar)

        # Mob filter
        layout.addWidget(QLabel("Mob:"))
        self.mob_filter = QComboBox()
        self.mob_filter.setMinimumWidth(150)
        self.mob_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.mob_filter)

        layout.addSpacing(20)

        # Date range
        layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        self.from_date.dateChanged.connect(self.refresh)
        layout.addWidget(self.from_date)

        layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        self.to_date.dateChanged.connect(self.refresh)
        layout.addWidget(self.to_date)

        layout.addStretch()

        return bar

    def _create_stats_row(self) -> QWidget:
        """Create the statistics summary row."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 10, 0, 10)

        # Stats cards
        self.total_weights_label = self._create_stat_card("Total Records", "0")
        layout.addWidget(self.total_weights_label)

        self.avg_weight_label = self._create_stat_card("Average Weight", "0 kg")
        layout.addWidget(self.avg_weight_label)

        self.avg_adg_label = self._create_stat_card("Average ADG", "0 kg/day")
        layout.addWidget(self.avg_adg_label)

        self.underperformers_label = self._create_stat_card("Underperformers", "0")
        layout.addWidget(self.underperformers_label)

        layout.addStretch()

        return container

    def _create_stat_card(self, title: str, value: str) -> QFrame:
        """Create a small stat card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                min-width: 120px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        return card

    def refresh(self) -> None:
        """Refresh weight data."""
        self._refresh_mob_filter()
        self._load_weights()
        self._update_stats()

    def _refresh_mob_filter(self) -> None:
        """Refresh the mob filter dropdown."""
        current = self.mob_filter.currentData()
        self.mob_filter.blockSignals(True)
        self.mob_filter.clear()
        self.mob_filter.addItem("All Mobs", None)

        for mob in self.db.get_all_mobs():
            self.mob_filter.addItem(mob.name, mob.id)

        if current:
            index = self.mob_filter.findData(current)
            if index >= 0:
                self.mob_filter.setCurrentIndex(index)

        self.mob_filter.blockSignals(False)

    def _load_weights(self) -> None:
        """Load weight records into the table."""
        self.table.setRowCount(0)

        mob_id = self.mob_filter.currentData()

        # Get date range
        from_qdate = self.from_date.date()
        to_qdate = self.to_date.date()
        from_date = date(from_qdate.year(), from_qdate.month(), from_qdate.day())
        to_date = date(to_qdate.year(), to_qdate.month(), to_qdate.day())

        # Get all weigh events
        events = self.db.get_recent_events(limit=500)
        weigh_events = [
            e for e in events
            if e.event_type == EventType.WEIGH
            and from_date <= e.event_date <= to_date
        ]

        # Track animal weights for ADG calculation
        animal_weights: dict[int, list[tuple[date, float]]] = {}

        for event in weigh_events:
            if not event.animal_id:
                continue

            animal = self.db.get_animal(event.animal_id)
            if not animal:
                continue

            # Filter by mob if selected
            if mob_id and animal.mob_id != mob_id:
                continue

            weigh = self.db.get_weigh_details(event.id)
            if not weigh:
                continue

            # Track for ADG
            if animal.id not in animal_weights:
                animal_weights[animal.id] = []
            animal_weights[animal.id].append((event.event_date, weigh.weight_kg))

            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(event.event_date)))
            self.table.setItem(row, 1, QTableWidgetItem(animal.display_id))
            self.table.setItem(row, 2, QTableWidgetItem(f"{weigh.weight_kg:.1f}"))

            cs = f"{weigh.condition_score:.1f}" if weigh.condition_score else "-"
            self.table.setItem(row, 3, QTableWidgetItem(cs))

            # Calculate ADG if we have previous weight
            adg = self._calculate_adg(animal.id, event.event_date, weigh.weight_kg, animal_weights)
            adg_str = f"{adg:.2f}" if adg is not None else "-"
            self.table.setItem(row, 4, QTableWidgetItem(adg_str))

            self.table.setItem(row, 5, QTableWidgetItem(event.notes[:30] if event.notes else ""))

    def _calculate_adg(
        self,
        animal_id: int,
        current_date: date,
        current_weight: float,
        animal_weights: dict[int, list[tuple[date, float]]],
    ) -> Optional[float]:
        """Calculate Average Daily Gain for an animal."""
        weights = animal_weights.get(animal_id, [])
        if len(weights) < 2:
            return None

        # Sort by date and find the previous weight
        sorted_weights = sorted(weights, key=lambda x: x[0])

        for i, (d, w) in enumerate(sorted_weights):
            if d == current_date:
                if i > 0:
                    prev_date, prev_weight = sorted_weights[i - 1]
                    days = (current_date - prev_date).days
                    if days > 0:
                        return (current_weight - prev_weight) / days
                break

        return None

    def _update_stats(self) -> None:
        """Update the statistics cards."""
        row_count = self.table.rowCount()

        # Total records
        total_label = self.total_weights_label.findChild(QLabel, "value")
        if total_label:
            total_label.setText(str(row_count))

        # Calculate averages from table data
        total_weight = 0.0
        total_adg = 0.0
        adg_count = 0
        underperformers = 0

        for row in range(row_count):
            weight_item = self.table.item(row, 2)
            if weight_item:
                try:
                    total_weight += float(weight_item.text())
                except ValueError:
                    pass

            adg_item = self.table.item(row, 4)
            if adg_item and adg_item.text() != "-":
                try:
                    adg = float(adg_item.text())
                    total_adg += adg
                    adg_count += 1
                    if adg < 0.5:  # Consider < 0.5 kg/day as underperforming
                        underperformers += 1
                except ValueError:
                    pass

        avg_weight_label = self.avg_weight_label.findChild(QLabel, "value")
        if avg_weight_label:
            avg = total_weight / row_count if row_count > 0 else 0
            avg_weight_label.setText(f"{avg:.1f} kg")

        avg_adg_label = self.avg_adg_label.findChild(QLabel, "value")
        if avg_adg_label:
            avg = total_adg / adg_count if adg_count > 0 else 0
            avg_adg_label.setText(f"{avg:.2f} kg/day")

        underperformers_label = self.underperformers_label.findChild(QLabel, "value")
        if underperformers_label:
            underperformers_label.setText(str(underperformers))

    def _on_record_weights(self) -> None:
        """Open the record weights dialog."""
        from stockbook.ui.dialogs.quick_actions import QuickWeighDialog

        # Get alive animals
        from stockbook.models.entities import AnimalStatus

        animals = self.db.get_all_animals(status=AnimalStatus.ALIVE)
        if not animals:
            QMessageBox.information(
                self, "No Animals", "No alive animals found. Add animals first."
            )
            return

        # For simplicity, open dialog for first animal
        # In a full implementation, you'd have a bulk weight entry screen
        dialog = QuickWeighDialog(self.db, [animals[0].id], parent=self)
        if dialog.exec():
            self.refresh()
