"""SQLite database management for Outback Stockbook."""

import sqlite3
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from stockbook.models.entities import (
    Animal,
    AnimalSex,
    AnimalStatus,
    Event,
    EventType,
    Mob,
    MovementEvent,
    Paddock,
    Product,
    PropertySettings,
    Species,
    Task,
    TreatmentEvent,
    TreatmentRoute,
    WeighEvent,
)


SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Property settings
CREATE TABLE IF NOT EXISTS property_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_name TEXT NOT NULL DEFAULT '',
    pic TEXT NOT NULL DEFAULT '',
    owner_name TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Paddocks
CREATE TABLE IF NOT EXISTS paddocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    area_hectares REAL,
    notes TEXT DEFAULT '',
    pic TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mobs
CREATE TABLE IF NOT EXISTS mobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT NOT NULL DEFAULT 'cattle',
    description TEXT DEFAULT '',
    current_paddock_id INTEGER REFERENCES paddocks(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Animals
CREATE TABLE IF NOT EXISTS animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eid TEXT DEFAULT '',
    visual_tag TEXT DEFAULT '',
    species TEXT NOT NULL DEFAULT 'cattle',
    breed TEXT DEFAULT '',
    sex TEXT NOT NULL DEFAULT 'female',
    date_of_birth DATE,
    status TEXT NOT NULL DEFAULT 'alive',
    mob_id INTEGER REFERENCES mobs(id),
    dam_id INTEGER REFERENCES animals(id),
    sire_id INTEGER REFERENCES animals(id),
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products (treatments)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    active_ingredient TEXT DEFAULT '',
    category TEXT DEFAULT '',
    meat_whp_days INTEGER DEFAULT 0,
    milk_whp_days INTEGER DEFAULT 0,
    esi_days INTEGER DEFAULT 0,
    default_dose TEXT DEFAULT '',
    default_route TEXT DEFAULT 'subcutaneous',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events (base table for all event types)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    animal_id INTEGER REFERENCES animals(id),
    mob_id INTEGER REFERENCES mobs(id),
    notes TEXT DEFAULT '',
    recorded_by TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Movement events
CREATE TABLE IF NOT EXISTS movement_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    from_paddock_id INTEGER REFERENCES paddocks(id),
    to_paddock_id INTEGER REFERENCES paddocks(id),
    reason TEXT DEFAULT '',
    head_count INTEGER DEFAULT 0
);

-- Treatment events
CREATE TABLE IF NOT EXISTS treatment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    batch_number TEXT DEFAULT '',
    dose TEXT DEFAULT '',
    route TEXT DEFAULT '',
    administered_by TEXT DEFAULT '',
    meat_whp_end DATE,
    milk_whp_end DATE,
    esi_end DATE
);

-- Weigh events
CREATE TABLE IF NOT EXISTS weigh_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    weight_kg REAL NOT NULL,
    condition_score REAL
);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    due_date DATE,
    source_event_id INTEGER REFERENCES events(id),
    animal_id INTEGER REFERENCES animals(id),
    mob_id INTEGER REFERENCES mobs(id),
    completed INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_animals_mob ON animals(mob_id);
CREATE INDEX IF NOT EXISTS idx_animals_status ON animals(status);
CREATE INDEX IF NOT EXISTS idx_animals_eid ON animals(eid);
CREATE INDEX IF NOT EXISTS idx_animals_visual_tag ON animals(visual_tag);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_animal ON events(animal_id);
CREATE INDEX IF NOT EXISTS idx_events_mob ON events(mob_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);
CREATE INDEX IF NOT EXISTS idx_treatment_whp ON treatment_events(meat_whp_end);
"""


class Database:
    """SQLite database manager for Outback Stockbook."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            # Default to user's data directory
            data_dir = Path.home() / ".outback-stockbook"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "stockbook.db"

        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open database connection and ensure schema exists."""
        self._conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Get the database connection, connecting if necessary."""
        if self._conn is None:
            self.connect()
        return self._conn

    def _init_schema(self) -> None:
        """Initialize database schema if needed."""
        cursor = self.conn.cursor()

        # Check if schema exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        if cursor.fetchone() is None:
            # Fresh database, create schema
            cursor.executescript(SCHEMA_SQL)
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            self.conn.commit()

    # -------------------------------------------------------------------------
    # Paddock operations
    # -------------------------------------------------------------------------

    def save_paddock(self, paddock: Paddock) -> Paddock:
        """Save a paddock (insert or update)."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if paddock.id is None:
            cursor.execute(
                """INSERT INTO paddocks (name, area_hectares, notes, pic, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (paddock.name, paddock.area_hectares, paddock.notes, paddock.pic, now, now),
            )
            paddock.id = cursor.lastrowid
            paddock.created_at = now
        else:
            cursor.execute(
                """UPDATE paddocks SET name=?, area_hectares=?, notes=?, pic=?, updated_at=?
                   WHERE id=?""",
                (paddock.name, paddock.area_hectares, paddock.notes, paddock.pic, now, paddock.id),
            )
        paddock.updated_at = now
        self.conn.commit()
        return paddock

    def get_paddock(self, paddock_id: int) -> Optional[Paddock]:
        """Get a paddock by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM paddocks WHERE id = ?", (paddock_id,))
        row = cursor.fetchone()
        return self._row_to_paddock(row) if row else None

    def get_all_paddocks(self) -> list[Paddock]:
        """Get all paddocks."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM paddocks ORDER BY name")
        return [self._row_to_paddock(row) for row in cursor.fetchall()]

    def delete_paddock(self, paddock_id: int) -> None:
        """Delete a paddock."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM paddocks WHERE id = ?", (paddock_id,))
        self.conn.commit()

    def _row_to_paddock(self, row: sqlite3.Row) -> Paddock:
        """Convert a database row to a Paddock object."""
        return Paddock(
            id=row["id"],
            name=row["name"],
            area_hectares=row["area_hectares"],
            notes=row["notes"],
            pic=row["pic"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # -------------------------------------------------------------------------
    # Mob operations
    # -------------------------------------------------------------------------

    def save_mob(self, mob: Mob) -> Mob:
        """Save a mob (insert or update)."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if mob.id is None:
            cursor.execute(
                """INSERT INTO mobs (name, species, description, current_paddock_id,
                   created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    mob.name,
                    mob.species.value,
                    mob.description,
                    mob.current_paddock_id,
                    now,
                    now,
                ),
            )
            mob.id = cursor.lastrowid
            mob.created_at = now
        else:
            cursor.execute(
                """UPDATE mobs SET name=?, species=?, description=?, current_paddock_id=?,
                   updated_at=? WHERE id=?""",
                (
                    mob.name,
                    mob.species.value,
                    mob.description,
                    mob.current_paddock_id,
                    now,
                    mob.id,
                ),
            )
        mob.updated_at = now
        self.conn.commit()
        return mob

    def get_mob(self, mob_id: int) -> Optional[Mob]:
        """Get a mob by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mobs WHERE id = ?", (mob_id,))
        row = cursor.fetchone()
        return self._row_to_mob(row) if row else None

    def get_all_mobs(self) -> list[Mob]:
        """Get all mobs."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mobs ORDER BY name")
        return [self._row_to_mob(row) for row in cursor.fetchall()]

    def delete_mob(self, mob_id: int) -> None:
        """Delete a mob."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM mobs WHERE id = ?", (mob_id,))
        self.conn.commit()

    def get_mob_animal_count(self, mob_id: int) -> int:
        """Get count of alive animals in a mob."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM animals WHERE mob_id = ? AND status = 'alive'", (mob_id,)
        )
        return cursor.fetchone()[0]

    def _row_to_mob(self, row: sqlite3.Row) -> Mob:
        """Convert a database row to a Mob object."""
        return Mob(
            id=row["id"],
            name=row["name"],
            species=Species(row["species"]),
            description=row["description"],
            current_paddock_id=row["current_paddock_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # -------------------------------------------------------------------------
    # Animal operations
    # -------------------------------------------------------------------------

    def save_animal(self, animal: Animal) -> Animal:
        """Save an animal (insert or update)."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if animal.id is None:
            cursor.execute(
                """INSERT INTO animals (eid, visual_tag, species, breed, sex, date_of_birth,
                   status, mob_id, dam_id, sire_id, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    animal.eid,
                    animal.visual_tag,
                    animal.species.value,
                    animal.breed,
                    animal.sex.value,
                    animal.date_of_birth,
                    animal.status.value,
                    animal.mob_id,
                    animal.dam_id,
                    animal.sire_id,
                    animal.notes,
                    now,
                    now,
                ),
            )
            animal.id = cursor.lastrowid
            animal.created_at = now
        else:
            cursor.execute(
                """UPDATE animals SET eid=?, visual_tag=?, species=?, breed=?, sex=?,
                   date_of_birth=?, status=?, mob_id=?, dam_id=?, sire_id=?, notes=?,
                   updated_at=? WHERE id=?""",
                (
                    animal.eid,
                    animal.visual_tag,
                    animal.species.value,
                    animal.breed,
                    animal.sex.value,
                    animal.date_of_birth,
                    animal.status.value,
                    animal.mob_id,
                    animal.dam_id,
                    animal.sire_id,
                    animal.notes,
                    now,
                    animal.id,
                ),
            )
        animal.updated_at = now
        self.conn.commit()
        return animal

    def get_animal(self, animal_id: int) -> Optional[Animal]:
        """Get an animal by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM animals WHERE id = ?", (animal_id,))
        row = cursor.fetchone()
        return self._row_to_animal(row) if row else None

    def get_animal_by_eid(self, eid: str) -> Optional[Animal]:
        """Get an animal by EID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM animals WHERE eid = ?", (eid,))
        row = cursor.fetchone()
        return self._row_to_animal(row) if row else None

    def get_all_animals(self, status: Optional[AnimalStatus] = None) -> list[Animal]:
        """Get all animals, optionally filtered by status."""
        cursor = self.conn.cursor()
        if status:
            cursor.execute(
                "SELECT * FROM animals WHERE status = ? ORDER BY visual_tag, eid",
                (status.value,),
            )
        else:
            cursor.execute("SELECT * FROM animals ORDER BY visual_tag, eid")
        return [self._row_to_animal(row) for row in cursor.fetchall()]

    def get_animals_by_mob(self, mob_id: int) -> list[Animal]:
        """Get all animals in a mob."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM animals WHERE mob_id = ? ORDER BY visual_tag, eid", (mob_id,)
        )
        return [self._row_to_animal(row) for row in cursor.fetchall()]

    def search_animals(self, query: str) -> list[Animal]:
        """Search animals by EID or visual tag."""
        cursor = self.conn.cursor()
        like_query = f"%{query}%"
        cursor.execute(
            """SELECT * FROM animals
               WHERE eid LIKE ? OR visual_tag LIKE ?
               ORDER BY visual_tag, eid""",
            (like_query, like_query),
        )
        return [self._row_to_animal(row) for row in cursor.fetchall()]

    def delete_animal(self, animal_id: int) -> None:
        """Delete an animal."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
        self.conn.commit()

    def _row_to_animal(self, row: sqlite3.Row) -> Animal:
        """Convert a database row to an Animal object."""
        return Animal(
            id=row["id"],
            eid=row["eid"],
            visual_tag=row["visual_tag"],
            species=Species(row["species"]),
            breed=row["breed"],
            sex=AnimalSex(row["sex"]),
            date_of_birth=row["date_of_birth"],
            status=AnimalStatus(row["status"]),
            mob_id=row["mob_id"],
            dam_id=row["dam_id"],
            sire_id=row["sire_id"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # -------------------------------------------------------------------------
    # Product operations
    # -------------------------------------------------------------------------

    def save_product(self, product: Product) -> Product:
        """Save a product (insert or update)."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if product.id is None:
            cursor.execute(
                """INSERT INTO products (name, active_ingredient, category, meat_whp_days,
                   milk_whp_days, esi_days, default_dose, default_route, notes,
                   created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    product.name,
                    product.active_ingredient,
                    product.category,
                    product.meat_whp_days,
                    product.milk_whp_days,
                    product.esi_days,
                    product.default_dose,
                    product.default_route.value,
                    product.notes,
                    now,
                    now,
                ),
            )
            product.id = cursor.lastrowid
            product.created_at = now
        else:
            cursor.execute(
                """UPDATE products SET name=?, active_ingredient=?, category=?, meat_whp_days=?,
                   milk_whp_days=?, esi_days=?, default_dose=?, default_route=?, notes=?,
                   updated_at=? WHERE id=?""",
                (
                    product.name,
                    product.active_ingredient,
                    product.category,
                    product.meat_whp_days,
                    product.milk_whp_days,
                    product.esi_days,
                    product.default_dose,
                    product.default_route.value,
                    product.notes,
                    now,
                    product.id,
                ),
            )
        product.updated_at = now
        self.conn.commit()
        return product

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return self._row_to_product(row) if row else None

    def get_all_products(self) -> list[Product]:
        """Get all products."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY name")
        return [self._row_to_product(row) for row in cursor.fetchall()]

    def delete_product(self, product_id: int) -> None:
        """Delete a product."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        """Convert a database row to a Product object."""
        return Product(
            id=row["id"],
            name=row["name"],
            active_ingredient=row["active_ingredient"],
            category=row["category"],
            meat_whp_days=row["meat_whp_days"],
            milk_whp_days=row["milk_whp_days"],
            esi_days=row["esi_days"],
            default_dose=row["default_dose"],
            default_route=TreatmentRoute(row["default_route"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # -------------------------------------------------------------------------
    # Event operations
    # -------------------------------------------------------------------------

    def save_event(self, event: Event) -> Event:
        """Save a base event."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if event.id is None:
            cursor.execute(
                """INSERT INTO events (event_type, event_date, animal_id, mob_id, notes,
                   recorded_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_type.value,
                    event.event_date,
                    event.animal_id,
                    event.mob_id,
                    event.notes,
                    event.recorded_by,
                    now,
                ),
            )
            event.id = cursor.lastrowid
            event.created_at = now
        else:
            cursor.execute(
                """UPDATE events SET event_type=?, event_date=?, animal_id=?, mob_id=?,
                   notes=?, recorded_by=? WHERE id=?""",
                (
                    event.event_type.value,
                    event.event_date,
                    event.animal_id,
                    event.mob_id,
                    event.notes,
                    event.recorded_by,
                    event.id,
                ),
            )
        self.conn.commit()
        return event

    def save_movement_event(
        self, event: Event, movement: MovementEvent
    ) -> tuple[Event, MovementEvent]:
        """Save a movement event with its details."""
        event.event_type = EventType.MOVEMENT
        event = self.save_event(event)

        cursor = self.conn.cursor()
        if movement.id is None:
            cursor.execute(
                """INSERT INTO movement_events (event_id, from_paddock_id, to_paddock_id,
                   reason, head_count) VALUES (?, ?, ?, ?, ?)""",
                (
                    event.id,
                    movement.from_paddock_id,
                    movement.to_paddock_id,
                    movement.reason,
                    movement.head_count,
                ),
            )
            movement.id = cursor.lastrowid
            movement.event_id = event.id
        else:
            cursor.execute(
                """UPDATE movement_events SET from_paddock_id=?, to_paddock_id=?, reason=?,
                   head_count=? WHERE id=?""",
                (
                    movement.from_paddock_id,
                    movement.to_paddock_id,
                    movement.reason,
                    movement.head_count,
                    movement.id,
                ),
            )
        self.conn.commit()
        return event, movement

    def save_treatment_event(
        self, event: Event, treatment: TreatmentEvent
    ) -> tuple[Event, TreatmentEvent]:
        """Save a treatment event with its details."""
        event.event_type = EventType.TREATMENT
        event = self.save_event(event)

        cursor = self.conn.cursor()
        if treatment.id is None:
            cursor.execute(
                """INSERT INTO treatment_events (event_id, product_id, batch_number, dose,
                   route, administered_by, meat_whp_end, milk_whp_end, esi_end)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.id,
                    treatment.product_id,
                    treatment.batch_number,
                    treatment.dose,
                    treatment.route.value,
                    treatment.administered_by,
                    treatment.meat_whp_end,
                    treatment.milk_whp_end,
                    treatment.esi_end,
                ),
            )
            treatment.id = cursor.lastrowid
            treatment.event_id = event.id
        else:
            cursor.execute(
                """UPDATE treatment_events SET product_id=?, batch_number=?, dose=?, route=?,
                   administered_by=?, meat_whp_end=?, milk_whp_end=?, esi_end=? WHERE id=?""",
                (
                    treatment.product_id,
                    treatment.batch_number,
                    treatment.dose,
                    treatment.route.value,
                    treatment.administered_by,
                    treatment.meat_whp_end,
                    treatment.milk_whp_end,
                    treatment.esi_end,
                    treatment.id,
                ),
            )
        self.conn.commit()
        return event, treatment

    def save_weigh_event(self, event: Event, weigh: WeighEvent) -> tuple[Event, WeighEvent]:
        """Save a weigh event with its details."""
        event.event_type = EventType.WEIGH
        event = self.save_event(event)

        cursor = self.conn.cursor()
        if weigh.id is None:
            cursor.execute(
                """INSERT INTO weigh_events (event_id, weight_kg, condition_score)
                   VALUES (?, ?, ?)""",
                (event.id, weigh.weight_kg, weigh.condition_score),
            )
            weigh.id = cursor.lastrowid
            weigh.event_id = event.id
        else:
            cursor.execute(
                "UPDATE weigh_events SET weight_kg=?, condition_score=? WHERE id=?",
                (weigh.weight_kg, weigh.condition_score, weigh.id),
            )
        self.conn.commit()
        return event, weigh

    def get_events_for_animal(
        self, animal_id: int, event_type: Optional[EventType] = None
    ) -> list[Event]:
        """Get events for an animal."""
        cursor = self.conn.cursor()
        if event_type:
            cursor.execute(
                """SELECT * FROM events WHERE animal_id = ? AND event_type = ?
                   ORDER BY event_date DESC""",
                (animal_id, event_type.value),
            )
        else:
            cursor.execute(
                "SELECT * FROM events WHERE animal_id = ? ORDER BY event_date DESC",
                (animal_id,),
            )
        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_events_for_mob(
        self, mob_id: int, event_type: Optional[EventType] = None
    ) -> list[Event]:
        """Get events for a mob."""
        cursor = self.conn.cursor()
        if event_type:
            cursor.execute(
                """SELECT * FROM events WHERE mob_id = ? AND event_type = ?
                   ORDER BY event_date DESC""",
                (mob_id, event_type.value),
            )
        else:
            cursor.execute(
                "SELECT * FROM events WHERE mob_id = ? ORDER BY event_date DESC",
                (mob_id,),
            )
        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_recent_events(self, limit: int = 50) -> list[Event]:
        """Get recent events across all animals/mobs."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM events ORDER BY event_date DESC, created_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_treatment_details(self, event_id: int) -> Optional[TreatmentEvent]:
        """Get treatment details for an event."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM treatment_events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if row:
            return TreatmentEvent(
                id=row["id"],
                event_id=row["event_id"],
                product_id=row["product_id"],
                batch_number=row["batch_number"],
                dose=row["dose"],
                route=TreatmentRoute(row["route"]) if row["route"] else TreatmentRoute.OTHER,
                administered_by=row["administered_by"],
                meat_whp_end=row["meat_whp_end"],
                milk_whp_end=row["milk_whp_end"],
                esi_end=row["esi_end"],
            )
        return None

    def get_movement_details(self, event_id: int) -> Optional[MovementEvent]:
        """Get movement details for an event."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM movement_events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if row:
            return MovementEvent(
                id=row["id"],
                event_id=row["event_id"],
                from_paddock_id=row["from_paddock_id"],
                to_paddock_id=row["to_paddock_id"],
                reason=row["reason"],
                head_count=row["head_count"],
            )
        return None

    def get_weigh_details(self, event_id: int) -> Optional[WeighEvent]:
        """Get weigh details for an event."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM weigh_events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if row:
            return WeighEvent(
                id=row["id"],
                event_id=row["event_id"],
                weight_kg=row["weight_kg"],
                condition_score=row["condition_score"],
            )
        return None

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """Convert a database row to an Event object."""
        return Event(
            id=row["id"],
            event_type=EventType(row["event_type"]),
            event_date=row["event_date"],
            animal_id=row["animal_id"],
            mob_id=row["mob_id"],
            notes=row["notes"],
            recorded_by=row["recorded_by"],
            created_at=row["created_at"],
        )

    # -------------------------------------------------------------------------
    # WHP (Withholding Period) queries
    # -------------------------------------------------------------------------

    def get_animals_on_whp(self, as_of_date: Optional[date] = None) -> list[dict]:
        """Get animals currently under withholding period.

        Returns list of dicts with animal, event, treatment, and product info.
        """
        if as_of_date is None:
            as_of_date = date.today()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                a.id as animal_id, a.eid, a.visual_tag,
                e.id as event_id, e.event_date,
                t.meat_whp_end, t.milk_whp_end, t.esi_end,
                p.name as product_name
            FROM treatment_events t
            JOIN events e ON t.event_id = e.id
            JOIN animals a ON e.animal_id = a.id
            LEFT JOIN products p ON t.product_id = p.id
            WHERE a.status = 'alive'
              AND (t.meat_whp_end >= ? OR t.milk_whp_end >= ? OR t.esi_end >= ?)
            ORDER BY t.meat_whp_end, a.visual_tag
            """,
            (as_of_date, as_of_date, as_of_date),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "animal_id": row["animal_id"],
                    "eid": row["eid"],
                    "visual_tag": row["visual_tag"],
                    "event_id": row["event_id"],
                    "event_date": row["event_date"],
                    "meat_whp_end": row["meat_whp_end"],
                    "milk_whp_end": row["milk_whp_end"],
                    "esi_end": row["esi_end"],
                    "product_name": row["product_name"],
                }
            )
        return results

    # -------------------------------------------------------------------------
    # Task operations
    # -------------------------------------------------------------------------

    def save_task(self, task: Task) -> Task:
        """Save a task."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if task.id is None:
            cursor.execute(
                """INSERT INTO tasks (title, description, due_date, source_event_id,
                   animal_id, mob_id, completed, completed_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.title,
                    task.description,
                    task.due_date,
                    task.source_event_id,
                    task.animal_id,
                    task.mob_id,
                    1 if task.completed else 0,
                    task.completed_at,
                    now,
                ),
            )
            task.id = cursor.lastrowid
            task.created_at = now
        else:
            cursor.execute(
                """UPDATE tasks SET title=?, description=?, due_date=?, source_event_id=?,
                   animal_id=?, mob_id=?, completed=?, completed_at=? WHERE id=?""",
                (
                    task.title,
                    task.description,
                    task.due_date,
                    task.source_event_id,
                    task.animal_id,
                    task.mob_id,
                    1 if task.completed else 0,
                    task.completed_at,
                    task.id,
                ),
            )
        self.conn.commit()
        return task

    def get_pending_tasks(self, days_ahead: int = 7) -> list[Task]:
        """Get pending tasks due within the specified days."""
        cursor = self.conn.cursor()
        from datetime import timedelta

        end_date = date.today() + timedelta(days=days_ahead)
        cursor.execute(
            """SELECT * FROM tasks
               WHERE completed = 0 AND (due_date IS NULL OR due_date <= ?)
               ORDER BY due_date NULLS LAST, created_at""",
            (end_date,),
        )
        return [self._row_to_task(row) for row in cursor.fetchall()]

    def complete_task(self, task_id: int) -> None:
        """Mark a task as completed."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE tasks SET completed = 1, completed_at = ? WHERE id = ?",
            (datetime.now(), task_id),
        )
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        """Delete a task."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert a database row to a Task object."""
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            due_date=row["due_date"],
            source_event_id=row["source_event_id"],
            animal_id=row["animal_id"],
            mob_id=row["mob_id"],
            completed=bool(row["completed"]),
            completed_at=row["completed_at"],
            created_at=row["created_at"],
        )

    # -------------------------------------------------------------------------
    # Property settings
    # -------------------------------------------------------------------------

    def get_property_settings(self) -> Optional[PropertySettings]:
        """Get property settings (creates default if none exist)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM property_settings LIMIT 1")
        row = cursor.fetchone()
        if row:
            return PropertySettings(
                id=row["id"],
                property_name=row["property_name"],
                pic=row["pic"],
                owner_name=row["owner_name"],
                address=row["address"],
                phone=row["phone"],
                email=row["email"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        return None

    def save_property_settings(self, settings: PropertySettings) -> PropertySettings:
        """Save property settings."""
        cursor = self.conn.cursor()
        now = datetime.now()

        if settings.id is None:
            cursor.execute(
                """INSERT INTO property_settings (property_name, pic, owner_name, address,
                   phone, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    settings.property_name,
                    settings.pic,
                    settings.owner_name,
                    settings.address,
                    settings.phone,
                    settings.email,
                    now,
                    now,
                ),
            )
            settings.id = cursor.lastrowid
            settings.created_at = now
        else:
            cursor.execute(
                """UPDATE property_settings SET property_name=?, pic=?, owner_name=?,
                   address=?, phone=?, email=?, updated_at=? WHERE id=?""",
                (
                    settings.property_name,
                    settings.pic,
                    settings.owner_name,
                    settings.address,
                    settings.phone,
                    settings.email,
                    now,
                    settings.id,
                ),
            )
        settings.updated_at = now
        self.conn.commit()
        return settings

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_animal_counts(self) -> dict[str, int]:
        """Get counts of animals by status."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT status, COUNT(*) as count FROM animals GROUP BY status"""
        )
        return {row["status"]: row["count"] for row in cursor.fetchall()}

    def get_species_counts(self) -> dict[str, int]:
        """Get counts of alive animals by species."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT species, COUNT(*) as count FROM animals
               WHERE status = 'alive' GROUP BY species"""
        )
        return {row["species"]: row["count"] for row in cursor.fetchall()}

    # -------------------------------------------------------------------------
    # Backup and restore
    # -------------------------------------------------------------------------

    def backup(self, backup_path: Path) -> None:
        """Create a backup of the database."""
        self.conn.commit()  # Ensure all changes are written
        shutil.copy2(self.db_path, backup_path)

    def restore(self, backup_path: Path) -> None:
        """Restore database from a backup."""
        self.close()
        shutil.copy2(backup_path, self.db_path)
        self.connect()
