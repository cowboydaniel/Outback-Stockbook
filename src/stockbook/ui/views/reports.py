"""Reports view for Outback Stockbook."""

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QFormLayout,
    QFileDialog,
    QFrame,
    QScrollArea,
    QCheckBox,
)
from PySide6.QtCore import Qt, QDate

from stockbook.models.database import Database
from stockbook.models.entities import AnimalStatus, EventType
from stockbook.ui.views.base import BaseView
from stockbook.services.pdf_reports import ReportGenerator


class ReportsView(BaseView):
    """View for generating and exporting reports."""

    def __init__(self, db: Database):
        super().__init__(db, "Reports")
        self.report_generator = ReportGenerator(db)
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Scroll area for report options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Header
        header = QLabel("Generate Reports")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        content_layout.addWidget(header)

        # Date range selector (common to most reports)
        date_group = QGroupBox("Date Range")
        date_layout = QFormLayout(date_group)

        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setDisplayFormat("dd/MM/yyyy")
        date_layout.addRow("From:", self.from_date)

        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("dd/MM/yyyy")
        date_layout.addRow("To:", self.to_date)

        content_layout.addWidget(date_group)

        # Report types
        reports_layout = QHBoxLayout()

        # Treatment Register
        treatment_card = self._create_report_card(
            "Treatment Register",
            "List of all treatments administered within the date range. "
            "Includes product, dose, batch numbers, and withholding periods.",
            self._generate_treatment_report,
        )
        reports_layout.addWidget(treatment_card)

        # Movement Log
        movement_card = self._create_report_card(
            "Movement Log",
            "Record of all animal and mob movements between paddocks. "
            "Useful for NLIS compliance and traceability.",
            self._generate_movement_report,
        )
        reports_layout.addWidget(movement_card)

        content_layout.addLayout(reports_layout)

        # Second row of reports
        reports_layout2 = QHBoxLayout()

        # WHP Clearance
        whp_card = self._create_report_card(
            "WHP Clearance List",
            "Animals currently under withholding period and their clearance dates. "
            "Critical before any sale or slaughter.",
            self._generate_whp_report,
        )
        reports_layout2.addWidget(whp_card)

        # Sale Draft Sheet
        sale_card = self._create_report_card(
            "Sale Draft Sheet",
            "Prepare a draft list for sale with tag numbers, weights, and notes. "
            "Excludes animals on WHP.",
            self._generate_sale_draft,
        )
        reports_layout2.addWidget(sale_card)

        content_layout.addLayout(reports_layout2)

        # Third row
        reports_layout3 = QHBoxLayout()

        # Animal Inventory
        inventory_card = self._create_report_card(
            "Animal Inventory",
            "Complete list of all animals by status, mob, and species. "
            "Good for annual stocktake.",
            self._generate_inventory_report,
        )
        reports_layout3.addWidget(inventory_card)

        # Weight Summary
        weight_card = self._create_report_card(
            "Weight Summary",
            "Summary of weights recorded within the date range with growth rates. "
            "Identify underperformers.",
            self._generate_weight_report,
        )
        reports_layout3.addWidget(weight_card)

        content_layout.addLayout(reports_layout3)

        content_layout.addStretch()

        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def _create_report_card(
        self, title: str, description: str, generate_func: callable
    ) -> QFrame:
        """Create a report card widget."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                min-width: 280px;
                max-width: 350px;
            }
        """)

        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(desc_label)

        layout.addStretch()

        generate_btn = QPushButton("Generate PDF")
        generate_btn.setObjectName("actionButton")
        generate_btn.clicked.connect(generate_func)
        layout.addWidget(generate_btn)

        return card

    def _get_date_range(self) -> tuple[date, date]:
        """Get the selected date range."""
        from_qdate = self.from_date.date()
        to_qdate = self.to_date.date()
        return (
            date(from_qdate.year(), from_qdate.month(), from_qdate.day()),
            date(to_qdate.year(), to_qdate.month(), to_qdate.day()),
        )

    def _get_save_path(self, default_name: str) -> Path | None:
        """Get the path to save the PDF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / default_name),
            "PDF Files (*.pdf)",
        )
        return Path(file_path) if file_path else None

    def _generate_treatment_report(self) -> None:
        """Generate treatment register report."""
        from_date, to_date = self._get_date_range()
        path = self._get_save_path(f"treatment_register_{from_date}_{to_date}.pdf")

        if path:
            try:
                self.report_generator.generate_treatment_register(path, from_date, to_date)
                QMessageBox.information(
                    self, "Report Generated", f"Treatment register saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")

    def _generate_movement_report(self) -> None:
        """Generate movement log report."""
        from_date, to_date = self._get_date_range()
        path = self._get_save_path(f"movement_log_{from_date}_{to_date}.pdf")

        if path:
            try:
                self.report_generator.generate_movement_log(path, from_date, to_date)
                QMessageBox.information(
                    self, "Report Generated", f"Movement log saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")

    def _generate_whp_report(self) -> None:
        """Generate WHP clearance report."""
        path = self._get_save_path(f"whp_clearance_{date.today()}.pdf")

        if path:
            try:
                self.report_generator.generate_whp_clearance(path)
                QMessageBox.information(
                    self, "Report Generated", f"WHP clearance list saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")

    def _generate_sale_draft(self) -> None:
        """Generate sale draft sheet."""
        path = self._get_save_path(f"sale_draft_{date.today()}.pdf")

        if path:
            try:
                self.report_generator.generate_sale_draft(path)
                QMessageBox.information(
                    self, "Report Generated", f"Sale draft sheet saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")

    def _generate_inventory_report(self) -> None:
        """Generate animal inventory report."""
        path = self._get_save_path(f"animal_inventory_{date.today()}.pdf")

        if path:
            try:
                self.report_generator.generate_inventory(path)
                QMessageBox.information(
                    self, "Report Generated", f"Animal inventory saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")

    def _generate_weight_report(self) -> None:
        """Generate weight summary report."""
        from_date, to_date = self._get_date_range()
        path = self._get_save_path(f"weight_summary_{from_date}_{to_date}.pdf")

        if path:
            try:
                self.report_generator.generate_weight_summary(path, from_date, to_date)
                QMessageBox.information(
                    self, "Report Generated", f"Weight summary saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")

    def refresh(self) -> None:
        """Refresh view (no-op for reports)."""
        pass
