"""PDF report generation for Outback Stockbook."""

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)

from stockbook.models.database import Database
from stockbook.models.entities import AnimalStatus, EventType


class ReportGenerator:
    """Generates PDF reports for Outback Stockbook."""

    def __init__(self, db: Database):
        self.db = db
        self.styles = getSampleStyleSheet()

        # Custom styles
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                spaceAfter=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ReportSubtitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.grey,
                spaceAfter=20,
            )
        )

    def _get_property_header(self) -> list:
        """Get property information for report header."""
        settings = self.db.get_property_settings()
        elements = []

        if settings and settings.property_name:
            elements.append(Paragraph(settings.property_name, self.styles["Heading2"]))
            if settings.pic:
                elements.append(Paragraph(f"PIC: {settings.pic}", self.styles["Normal"]))

        return elements

    def _create_table(
        self, data: list[list], col_widths: list[float] = None
    ) -> Table:
        """Create a styled table."""
        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ]
            )
        )
        return table

    def generate_treatment_register(
        self, path: Path, from_date: date, to_date: date
    ) -> None:
        """Generate treatment register PDF."""
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        elements = []

        # Header
        elements.extend(self._get_property_header())
        elements.append(Paragraph("Treatment Register", self.styles["ReportTitle"]))
        elements.append(
            Paragraph(
                f"Period: {from_date.strftime('%d/%m/%Y')} to {to_date.strftime('%d/%m/%Y')}",
                self.styles["ReportSubtitle"],
            )
        )

        # Get treatment events
        events = self.db.get_recent_events(limit=1000)
        treatment_events = [
            e
            for e in events
            if e.event_type == EventType.TREATMENT
            and from_date <= e.event_date <= to_date
        ]

        if not treatment_events:
            elements.append(Paragraph("No treatments recorded in this period.", self.styles["Normal"]))
        else:
            # Build table data
            data = [["Date", "Animal/Mob", "Product", "Dose", "Batch", "WHP End", "By"]]

            products = {p.id: p.name for p in self.db.get_all_products()}

            for event in treatment_events:
                treatment = self.db.get_treatment_details(event.id)
                if not treatment:
                    continue

                # Get identifier
                identifier = ""
                if event.animal_id:
                    animal = self.db.get_animal(event.animal_id)
                    if animal:
                        identifier = animal.display_id
                elif event.mob_id:
                    mob = self.db.get_mob(event.mob_id)
                    if mob:
                        identifier = f"Mob: {mob.name}"

                whp_end = ""
                if treatment.meat_whp_end:
                    whp_end = treatment.meat_whp_end.strftime("%d/%m/%Y")

                data.append([
                    event.event_date.strftime("%d/%m/%Y"),
                    identifier,
                    products.get(treatment.product_id, "Unknown"),
                    treatment.dose,
                    treatment.batch_number,
                    whp_end,
                    treatment.administered_by,
                ])

            table = self._create_table(data, col_widths=[55, 80, 80, 60, 60, 70, 60])
            elements.append(table)

        # Footer
        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph(
                f"Generated: {date.today().strftime('%d/%m/%Y')}",
                self.styles["Normal"],
            )
        )

        doc.build(elements)

    def generate_movement_log(
        self, path: Path, from_date: date, to_date: date
    ) -> None:
        """Generate movement log PDF."""
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        elements = []

        # Header
        elements.extend(self._get_property_header())
        elements.append(Paragraph("Movement Log", self.styles["ReportTitle"]))
        elements.append(
            Paragraph(
                f"Period: {from_date.strftime('%d/%m/%Y')} to {to_date.strftime('%d/%m/%Y')}",
                self.styles["ReportSubtitle"],
            )
        )

        # Get movement events
        events = self.db.get_recent_events(limit=1000)
        movement_events = [
            e
            for e in events
            if e.event_type == EventType.MOVEMENT
            and from_date <= e.event_date <= to_date
        ]

        if not movement_events:
            elements.append(Paragraph("No movements recorded in this period.", self.styles["Normal"]))
        else:
            data = [["Date", "Animal/Mob", "From", "To", "Reason", "Head Count"]]

            paddocks = {p.id: p.name for p in self.db.get_all_paddocks()}

            for event in movement_events:
                movement = self.db.get_movement_details(event.id)
                if not movement:
                    continue

                identifier = ""
                if event.animal_id:
                    animal = self.db.get_animal(event.animal_id)
                    if animal:
                        identifier = animal.display_id
                elif event.mob_id:
                    mob = self.db.get_mob(event.mob_id)
                    if mob:
                        identifier = mob.name

                from_paddock = paddocks.get(movement.from_paddock_id, "-")
                to_paddock = paddocks.get(movement.to_paddock_id, "-")

                data.append([
                    event.event_date.strftime("%d/%m/%Y"),
                    identifier,
                    from_paddock,
                    to_paddock,
                    movement.reason or "-",
                    str(movement.head_count) if movement.head_count else "-",
                ])

            table = self._create_table(data)
            elements.append(table)

        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph(
                f"Generated: {date.today().strftime('%d/%m/%Y')}",
                self.styles["Normal"],
            )
        )

        doc.build(elements)

    def generate_whp_clearance(self, path: Path) -> None:
        """Generate WHP clearance list PDF."""
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        elements = []

        # Header
        elements.extend(self._get_property_header())
        elements.append(Paragraph("WHP Clearance List", self.styles["ReportTitle"]))
        elements.append(
            Paragraph(
                f"As of: {date.today().strftime('%d/%m/%Y')}",
                self.styles["ReportSubtitle"],
            )
        )

        # Warning
        elements.append(
            Paragraph(
                "IMPORTANT: Animals listed below are currently under withholding period "
                "and must NOT be sold for slaughter until their clearance date.",
                ParagraphStyle(
                    name="Warning",
                    parent=self.styles["Normal"],
                    textColor=colors.red,
                    fontSize=10,
                    spaceAfter=15,
                ),
            )
        )

        whp_animals = self.db.get_animals_on_whp()

        if not whp_animals:
            elements.append(
                Paragraph(
                    "No animals currently under withholding period. All clear for sale.",
                    ParagraphStyle(
                        name="Success",
                        parent=self.styles["Normal"],
                        textColor=colors.green,
                        fontSize=12,
                    ),
                )
            )
        else:
            data = [["Tag", "EID", "Product", "Treatment Date", "Meat WHP End", "Days Left"]]

            today = date.today()

            for item in whp_animals:
                days_left = ""
                if item["meat_whp_end"]:
                    days_left = str((item["meat_whp_end"] - today).days)

                data.append([
                    item["visual_tag"] or "-",
                    item["eid"] or "-",
                    item["product_name"] or "Unknown",
                    str(item["event_date"]) if item["event_date"] else "-",
                    item["meat_whp_end"].strftime("%d/%m/%Y") if item["meat_whp_end"] else "-",
                    days_left,
                ])

            table = self._create_table(data)
            elements.append(table)

        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph(
                f"Generated: {date.today().strftime('%d/%m/%Y')}",
                self.styles["Normal"],
            )
        )

        doc.build(elements)

    def generate_sale_draft(self, path: Path) -> None:
        """Generate sale draft sheet PDF."""
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        elements = []

        # Header
        elements.extend(self._get_property_header())
        elements.append(Paragraph("Sale Draft Sheet", self.styles["ReportTitle"]))
        elements.append(
            Paragraph(
                f"Prepared: {date.today().strftime('%d/%m/%Y')}",
                self.styles["ReportSubtitle"],
            )
        )

        # Get alive animals not on WHP
        whp_animal_ids = {item["animal_id"] for item in self.db.get_animals_on_whp()}
        all_animals = self.db.get_all_animals(status=AnimalStatus.ALIVE)
        sale_ready = [a for a in all_animals if a.id not in whp_animal_ids]

        if not sale_ready:
            elements.append(
                Paragraph("No animals available for sale (all on WHP or none alive).", self.styles["Normal"])
            )
        else:
            # Group by mob
            mobs = {m.id: m.name for m in self.db.get_all_mobs()}

            data = [["Tag", "EID", "Species", "Breed", "Sex", "Mob", "Notes"]]

            for animal in sale_ready:
                data.append([
                    animal.visual_tag or "-",
                    animal.eid or "-",
                    animal.species.value.title(),
                    animal.breed or "-",
                    animal.sex.value.title(),
                    mobs.get(animal.mob_id, "-"),
                    "",  # Empty notes column for handwriting
                ])

            table = self._create_table(data, col_widths=[50, 70, 50, 60, 50, 70, 100])
            elements.append(table)

            elements.append(Spacer(1, 15))
            elements.append(
                Paragraph(f"Total animals ready for sale: {len(sale_ready)}", self.styles["Heading3"])
            )

        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph(
                f"Generated: {date.today().strftime('%d/%m/%Y')}",
                self.styles["Normal"],
            )
        )

        doc.build(elements)

    def generate_inventory(self, path: Path) -> None:
        """Generate animal inventory PDF."""
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        elements = []

        # Header
        elements.extend(self._get_property_header())
        elements.append(Paragraph("Animal Inventory", self.styles["ReportTitle"]))
        elements.append(
            Paragraph(
                f"As of: {date.today().strftime('%d/%m/%Y')}",
                self.styles["ReportSubtitle"],
            )
        )

        # Summary counts
        counts = self.db.get_animal_counts()
        species_counts = self.db.get_species_counts()

        elements.append(Paragraph("Summary", self.styles["Heading2"]))

        summary_data = [["Status", "Count"]]
        for status, count in counts.items():
            summary_data.append([status.title(), str(count)])
        summary_data.append(["Total", str(sum(counts.values()))])

        summary_table = self._create_table(summary_data, col_widths=[150, 100])
        elements.append(summary_table)
        elements.append(Spacer(1, 15))

        # Alive animals by species
        elements.append(Paragraph("Alive by Species", self.styles["Heading3"]))
        species_data = [["Species", "Count"]]
        for species, count in species_counts.items():
            species_data.append([species.title(), str(count)])

        species_table = self._create_table(species_data, col_widths=[150, 100])
        elements.append(species_table)
        elements.append(Spacer(1, 20))

        # Full animal list
        elements.append(Paragraph("Complete Animal List", self.styles["Heading2"]))

        all_animals = self.db.get_all_animals()
        mobs = {m.id: m.name for m in self.db.get_all_mobs()}

        if all_animals:
            data = [["Tag", "EID", "Species", "Breed", "Sex", "Status", "Mob"]]

            for animal in all_animals:
                data.append([
                    animal.visual_tag or "-",
                    animal.eid or "-",
                    animal.species.value.title(),
                    animal.breed or "-",
                    animal.sex.value.title(),
                    animal.status.value.title(),
                    mobs.get(animal.mob_id, "-"),
                ])

            table = self._create_table(data)
            elements.append(table)
        else:
            elements.append(Paragraph("No animals in database.", self.styles["Normal"]))

        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph(
                f"Generated: {date.today().strftime('%d/%m/%Y')}",
                self.styles["Normal"],
            )
        )

        doc.build(elements)

    def generate_weight_summary(
        self, path: Path, from_date: date, to_date: date
    ) -> None:
        """Generate weight summary PDF."""
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        elements = []

        # Header
        elements.extend(self._get_property_header())
        elements.append(Paragraph("Weight Summary", self.styles["ReportTitle"]))
        elements.append(
            Paragraph(
                f"Period: {from_date.strftime('%d/%m/%Y')} to {to_date.strftime('%d/%m/%Y')}",
                self.styles["ReportSubtitle"],
            )
        )

        # Get weight events
        events = self.db.get_recent_events(limit=1000)
        weight_events = [
            e
            for e in events
            if e.event_type == EventType.WEIGH
            and from_date <= e.event_date <= to_date
        ]

        if not weight_events:
            elements.append(Paragraph("No weights recorded in this period.", self.styles["Normal"]))
        else:
            data = [["Date", "Animal", "Weight (kg)", "Condition Score"]]

            for event in weight_events:
                weigh = self.db.get_weigh_details(event.id)
                if not weigh:
                    continue

                identifier = ""
                if event.animal_id:
                    animal = self.db.get_animal(event.animal_id)
                    if animal:
                        identifier = animal.display_id

                cs = f"{weigh.condition_score:.1f}" if weigh.condition_score else "-"

                data.append([
                    event.event_date.strftime("%d/%m/%Y"),
                    identifier,
                    f"{weigh.weight_kg:.1f}",
                    cs,
                ])

            table = self._create_table(data)
            elements.append(table)

            # Summary stats
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("Statistics", self.styles["Heading3"]))

            weights = [
                self.db.get_weigh_details(e.id).weight_kg
                for e in weight_events
                if self.db.get_weigh_details(e.id)
            ]

            if weights:
                avg_weight = sum(weights) / len(weights)
                min_weight = min(weights)
                max_weight = max(weights)

                stats_text = (
                    f"Total records: {len(weights)}<br/>"
                    f"Average weight: {avg_weight:.1f} kg<br/>"
                    f"Minimum weight: {min_weight:.1f} kg<br/>"
                    f"Maximum weight: {max_weight:.1f} kg"
                )
                elements.append(Paragraph(stats_text, self.styles["Normal"]))

        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph(
                f"Generated: {date.today().strftime('%d/%m/%Y')}",
                self.styles["Normal"],
            )
        )

        doc.build(elements)
