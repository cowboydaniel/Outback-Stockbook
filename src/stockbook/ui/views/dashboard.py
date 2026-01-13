"""Dashboard view for Outback Stockbook."""

from datetime import date, timedelta

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
)
from PySide6.QtCore import Qt

from stockbook.models.database import Database
from stockbook.models.entities import EventType
from stockbook.ui.views.base import BaseView


class DashboardView(BaseView):
    """Main dashboard showing overview and alerts."""

    def __init__(self, db: Database):
        super().__init__(db, "Dashboard")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dashboard UI."""
        # Scroll area for dashboard content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Stats cards row
        stats_row = self._create_stats_row()
        content_layout.addWidget(stats_row)

        # Two-column layout for main content
        columns = QWidget()
        columns_layout = QHBoxLayout(columns)
        columns_layout.setSpacing(20)

        # Left column: WHP alerts and Tasks
        left_col = self._create_left_column()
        columns_layout.addWidget(left_col)

        # Right column: Recent activity
        right_col = self._create_right_column()
        columns_layout.addWidget(right_col)

        content_layout.addWidget(columns)
        content_layout.addStretch()

        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def _create_stats_row(self) -> QWidget:
        """Create the row of statistic cards."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder cards - will be populated in refresh()
        self.stats_cards = {}

        card_configs = [
            ("total_animals", "Total Animals", "0", "#3498db"),
            ("cattle", "Cattle", "0", "#27ae60"),
            ("sheep", "Sheep", "0", "#9b59b6"),
            ("on_whp", "On WHP", "0", "#e74c3c"),
            ("tasks_due", "Tasks Due", "0", "#f39c12"),
        ]

        for key, title, default_value, color in card_configs:
            card = self._create_stat_card(title, default_value, color)
            self.stats_cards[key] = card
            layout.addWidget(card["widget"])

        layout.addStretch()
        return container

    def _create_stat_card(self, title: str, value: str, color: str) -> dict:
        """Create a statistics card widget."""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background-color: #ffffff;
                border-left: 4px solid {color};
                border-radius: 8px;
                min-width: 150px;
                max-width: 200px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)

        return {"widget": card, "value_label": value_label, "title_label": title_label}

    def _create_left_column(self) -> QWidget:
        """Create the left column with WHP alerts and tasks."""
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # WHP Alerts section
        whp_section = self._create_whp_section()
        layout.addWidget(whp_section)

        # Tasks section
        tasks_section = self._create_tasks_section()
        layout.addWidget(tasks_section)

        layout.addStretch()
        return column

    def _create_whp_section(self) -> QWidget:
        """Create the Withholding Period alerts section."""
        section = QFrame()
        section.setObjectName("card")
        layout = QVBoxLayout(section)

        # Header
        header = QLabel("Animals on Withholding Period")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(header)

        # Table for WHP animals
        self.whp_table = QTableWidget()
        self.whp_table.setColumnCount(4)
        self.whp_table.setHorizontalHeaderLabels(["Tag", "Product", "Meat WHP End", "Days Left"])
        self.whp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.whp_table.setMaximumHeight(200)
        self.whp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.whp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.whp_table)

        # Empty state label
        self.whp_empty = QLabel("No animals currently on withholding period")
        self.whp_empty.setStyleSheet("color: #27ae60; font-style: italic; padding: 20px;")
        self.whp_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.whp_empty.hide()
        layout.addWidget(self.whp_empty)

        return section

    def _create_tasks_section(self) -> QWidget:
        """Create the Tasks/Reminders section."""
        section = QFrame()
        section.setObjectName("card")
        layout = QVBoxLayout(section)

        # Header with action button
        header_row = QHBoxLayout()
        header = QLabel("Tasks Due (Next 7 Days)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12;")
        header_row.addWidget(header)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Tasks list
        self.tasks_container = QVBoxLayout()
        layout.addLayout(self.tasks_container)

        # Empty state
        self.tasks_empty = QLabel("No tasks due - you're all caught up!")
        self.tasks_empty.setStyleSheet("color: #27ae60; font-style: italic; padding: 20px;")
        self.tasks_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tasks_empty.hide()
        layout.addWidget(self.tasks_empty)

        return section

    def _create_right_column(self) -> QWidget:
        """Create the right column with recent activity."""
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Recent events section
        events_section = self._create_events_section()
        layout.addWidget(events_section)

        layout.addStretch()
        return column

    def _create_events_section(self) -> QWidget:
        """Create the recent events section."""
        section = QFrame()
        section.setObjectName("card")
        layout = QVBoxLayout(section)

        # Header
        header = QLabel("Recent Activity")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        layout.addWidget(header)

        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(["Date", "Type", "Animal/Mob", "Notes"])
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.events_table.setMaximumHeight(400)
        self.events_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.events_table)

        # Empty state
        self.events_empty = QLabel("No recent activity - start by adding animals or paddocks")
        self.events_empty.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
        self.events_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.events_empty.hide()
        layout.addWidget(self.events_empty)

        return section

    def refresh(self) -> None:
        """Refresh dashboard data."""
        self._refresh_stats()
        self._refresh_whp()
        self._refresh_tasks()
        self._refresh_events()

    def _refresh_stats(self) -> None:
        """Refresh the statistics cards."""
        # Animal counts by status
        status_counts = self.db.get_animal_counts()
        total = sum(status_counts.values())
        alive = status_counts.get("alive", 0)

        # Species counts (alive only)
        species_counts = self.db.get_species_counts()
        cattle = species_counts.get("cattle", 0)
        sheep = species_counts.get("sheep", 0)

        # WHP count
        whp_animals = self.db.get_animals_on_whp()
        whp_count = len(whp_animals)

        # Tasks due
        tasks = self.db.get_pending_tasks(days_ahead=7)
        tasks_count = len(tasks)

        # Update cards
        self.stats_cards["total_animals"]["value_label"].setText(str(alive))
        self.stats_cards["cattle"]["value_label"].setText(str(cattle))
        self.stats_cards["sheep"]["value_label"].setText(str(sheep))
        self.stats_cards["on_whp"]["value_label"].setText(str(whp_count))
        self.stats_cards["tasks_due"]["value_label"].setText(str(tasks_count))

    def _refresh_whp(self) -> None:
        """Refresh the WHP alerts table."""
        whp_animals = self.db.get_animals_on_whp()

        self.whp_table.setRowCount(0)

        if not whp_animals:
            self.whp_table.hide()
            self.whp_empty.show()
            return

        self.whp_table.show()
        self.whp_empty.hide()

        today = date.today()
        for animal in whp_animals:
            row = self.whp_table.rowCount()
            self.whp_table.insertRow(row)

            tag = animal["visual_tag"] or animal["eid"] or f"#{animal['animal_id']}"
            self.whp_table.setItem(row, 0, QTableWidgetItem(tag))
            self.whp_table.setItem(row, 1, QTableWidgetItem(animal["product_name"] or "Unknown"))

            whp_end = animal["meat_whp_end"]
            if whp_end:
                self.whp_table.setItem(row, 2, QTableWidgetItem(str(whp_end)))
                days_left = (whp_end - today).days
                days_item = QTableWidgetItem(str(days_left))
                if days_left <= 3:
                    days_item.setBackground(Qt.GlobalColor.red)
                    days_item.setForeground(Qt.GlobalColor.white)
                elif days_left <= 7:
                    days_item.setBackground(Qt.GlobalColor.yellow)
                self.whp_table.setItem(row, 3, days_item)
            else:
                self.whp_table.setItem(row, 2, QTableWidgetItem("N/A"))
                self.whp_table.setItem(row, 3, QTableWidgetItem("-"))

    def _refresh_tasks(self) -> None:
        """Refresh the tasks section."""
        # Clear existing task widgets
        while self.tasks_container.count():
            item = self.tasks_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = self.db.get_pending_tasks(days_ahead=7)

        if not tasks:
            self.tasks_empty.show()
            return

        self.tasks_empty.hide()

        for task in tasks[:10]:  # Show max 10 tasks
            task_widget = self._create_task_item(task)
            self.tasks_container.addWidget(task_widget)

    def _create_task_item(self, task) -> QWidget:
        """Create a task list item widget."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-left: 3px solid #f39c12;
                padding: 5px;
                margin: 2px 0;
            }
        """)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(10, 8, 10, 8)

        # Task info
        info_layout = QVBoxLayout()
        title = QLabel(task.title)
        title.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(title)

        if task.due_date:
            due = QLabel(f"Due: {task.due_date}")
            due.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            info_layout.addWidget(due)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Complete button
        complete_btn = QPushButton("Done")
        complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                min-height: 30px;
                min-width: 60px;
                font-size: 11px;
            }
        """)
        complete_btn.clicked.connect(lambda: self._complete_task(task.id))
        layout.addWidget(complete_btn)

        return item

    def _complete_task(self, task_id: int) -> None:
        """Mark a task as completed."""
        self.db.complete_task(task_id)
        self._refresh_tasks()
        self._refresh_stats()

    def _refresh_events(self) -> None:
        """Refresh the recent events table."""
        events = self.db.get_recent_events(limit=20)

        self.events_table.setRowCount(0)

        if not events:
            self.events_table.hide()
            self.events_empty.show()
            return

        self.events_table.show()
        self.events_empty.hide()

        for event in events:
            row = self.events_table.rowCount()
            self.events_table.insertRow(row)

            self.events_table.setItem(row, 0, QTableWidgetItem(str(event.event_date)))
            self.events_table.setItem(row, 1, QTableWidgetItem(event.event_type.value.title()))

            # Get animal or mob identifier
            identifier = ""
            if event.animal_id:
                animal = self.db.get_animal(event.animal_id)
                if animal:
                    identifier = animal.display_id
            elif event.mob_id:
                mob = self.db.get_mob(event.mob_id)
                if mob:
                    identifier = mob.name

            self.events_table.setItem(row, 2, QTableWidgetItem(identifier))
            self.events_table.setItem(row, 3, QTableWidgetItem(event.notes[:50] if event.notes else ""))
