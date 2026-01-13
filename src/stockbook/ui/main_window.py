"""Main application window for Outback Stockbook."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLineEdit,
    QLabel,
    QButtonGroup,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut

from stockbook import __app_name__, __version__
from stockbook.models.database import Database
from stockbook.ui.views.dashboard import DashboardView
from stockbook.ui.views.animals import AnimalsView
from stockbook.ui.views.mobs import MobsView
from stockbook.ui.views.paddocks import PaddocksView
from stockbook.ui.views.treatments import TreatmentsView
from stockbook.ui.views.weights import WeightsView
from stockbook.ui.views.reports import ReportsView
from stockbook.ui.views.settings import SettingsView


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setMinimumSize(1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Create content area
        content_area = self._create_content_area()
        main_layout.addWidget(content_area, 1)

        # Set up keyboard shortcuts
        self._setup_shortcuts()

        # Show dashboard by default
        self.nav_buttons[0].setChecked(True)
        self._on_nav_clicked(0)

    def _create_sidebar(self) -> QWidget:
        """Create the navigation sidebar."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Outback")
        title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title)

        subtitle = QLabel("Stockbook")
        subtitle.setStyleSheet("color: #3498db; font-size: 18px; font-weight: bold;")
        title_layout.addWidget(subtitle)

        layout.addWidget(title_container)

        # Navigation buttons
        nav_items = [
            ("Dashboard", "Home & overview"),
            ("Animals", "Individual animals"),
            ("Mobs", "Animal groups"),
            ("Paddocks", "Property areas"),
            ("Treatments", "Health & WHP"),
            ("Weights", "Weight records"),
            ("Reports", "Print & export"),
            ("Settings", "Backup & config"),
        ]

        self.nav_buttons: list[QPushButton] = []
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for i, (label, tooltip) in enumerate(nav_items):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            self.nav_buttons.append(btn)
            self.nav_group.addButton(btn, i)
            layout.addWidget(btn)

        self.nav_group.idClicked.connect(self._on_nav_clicked)

        # Spacer
        layout.addStretch()

        # Version info at bottom
        version_label = QLabel(f"v{__version__}")
        version_label.setStyleSheet("color: #7f8c8d; padding: 10px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """Create the main content area with search and views."""
        content = QFrame()
        content.setObjectName("content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar with search
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)

        # Stacked widget for views
        self.view_stack = QStackedWidget()
        self.view_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create all views
        self.views = [
            DashboardView(self.db),
            AnimalsView(self.db),
            MobsView(self.db),
            PaddocksView(self.db),
            TreatmentsView(self.db),
            WeightsView(self.db),
            ReportsView(self.db),
            SettingsView(self.db),
        ]

        for view in self.views:
            self.view_stack.addWidget(view)

        layout.addWidget(self.view_stack)

        return content

    def _create_top_bar(self) -> QWidget:
        """Create the top bar with search functionality."""
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #ecf0f1; border-bottom: 2px solid #bdc3c7;")
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Search by tag, EID, or mob name... (Ctrl+F)")
        self.search_bar.setMaximumWidth(500)
        self.search_bar.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_bar)

        layout.addStretch()

        # Current view title
        self.view_title = QLabel("Dashboard")
        self.view_title.setObjectName("titleLabel")
        layout.addWidget(self.view_title)

        return top_bar

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for navigation."""
        # Search shortcut
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._focus_search)

        # Navigation shortcuts (Alt+1 through Alt+8)
        for i in range(8):
            shortcut = QShortcut(QKeySequence(f"Alt+{i + 1}"), self)
            shortcut.activated.connect(lambda idx=i: self._navigate_to(idx))

        # Escape to clear search
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self._clear_search)

    def _on_nav_clicked(self, index: int) -> None:
        """Handle navigation button click."""
        self.view_stack.setCurrentIndex(index)

        # Update title
        titles = [
            "Dashboard",
            "Animals",
            "Mobs",
            "Paddocks",
            "Treatments",
            "Weights",
            "Reports",
            "Settings",
        ]
        self.view_title.setText(titles[index])

        # Refresh the view
        self.views[index].refresh()

    def _navigate_to(self, index: int) -> None:
        """Navigate to a specific view by index."""
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
            self._on_nav_clicked(index)

    def _focus_search(self) -> None:
        """Focus the search bar."""
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _clear_search(self) -> None:
        """Clear the search bar."""
        self.search_bar.clear()
        self.search_bar.clearFocus()

    def _on_search(self) -> None:
        """Handle search submission."""
        query = self.search_bar.text().strip()
        if query:
            # Switch to animals view and search
            self._navigate_to(1)  # Animals view
            animals_view = self.views[1]
            if hasattr(animals_view, "search"):
                animals_view.search(query)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Could add confirmation dialog here if needed
        event.accept()
