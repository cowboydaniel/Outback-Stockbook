"""Domain entities for Outback Stockbook."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class AnimalStatus(Enum):
    """Status of an animal in the herd."""

    ALIVE = "alive"
    SOLD = "sold"
    DEAD = "dead"
    MISSING = "missing"


class AnimalSex(Enum):
    """Sex of an animal."""

    MALE = "male"
    FEMALE = "female"
    STEER = "steer"  # Castrated male cattle
    WETHER = "wether"  # Castrated male sheep


class Species(Enum):
    """Species of livestock."""

    CATTLE = "cattle"
    SHEEP = "sheep"


class EventType(Enum):
    """Types of events that can be recorded."""

    MOVEMENT = "movement"
    TREATMENT = "treatment"
    WEIGH = "weigh"
    DEATH = "death"
    SALE = "sale"
    BIRTH = "birth"
    PREGNANCY_TEST = "pregnancy_test"
    JOINING = "joining"
    NOTE = "note"


class TreatmentRoute(Enum):
    """Route of treatment administration."""

    ORAL = "oral"
    INJECTION_SC = "subcutaneous"
    INJECTION_IM = "intramuscular"
    POUR_ON = "pour_on"
    SPRAY = "spray"
    EAR_TAG = "ear_tag"
    INTRARUMINAL = "intraruminal"
    OTHER = "other"


@dataclass
class Paddock:
    """A paddock or pasture area on the property."""

    id: Optional[int] = None
    name: str = ""
    area_hectares: Optional[float] = None
    notes: str = ""
    pic: str = ""  # Property Identification Code
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Mob:
    """A mob (group) of animals managed together."""

    id: Optional[int] = None
    name: str = ""
    species: Species = Species.CATTLE
    description: str = ""
    current_paddock_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Animal:
    """An individual animal in the herd/flock."""

    id: Optional[int] = None
    eid: str = ""  # Electronic ID (NLIS tag number)
    visual_tag: str = ""  # Visual tag number
    species: Species = Species.CATTLE
    breed: str = ""
    sex: AnimalSex = AnimalSex.FEMALE
    date_of_birth: Optional[date] = None
    status: AnimalStatus = AnimalStatus.ALIVE
    mob_id: Optional[int] = None
    dam_id: Optional[int] = None  # Mother
    sire_id: Optional[int] = None  # Father
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def display_id(self) -> str:
        """Return the best identifier for display."""
        return self.visual_tag or self.eid or f"#{self.id}"


@dataclass
class Product:
    """A treatment product (drench, vaccine, etc.)."""

    id: Optional[int] = None
    name: str = ""
    active_ingredient: str = ""
    category: str = ""  # e.g., "Drench", "Vaccine", "Antibiotic"
    meat_whp_days: int = 0  # Meat withholding period in days
    milk_whp_days: int = 0  # Milk withholding period in days
    esi_days: int = 0  # Export slaughter interval in days
    default_dose: str = ""  # e.g., "1ml/10kg"
    default_route: TreatmentRoute = TreatmentRoute.INJECTION_SC
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Event:
    """Base event record for all animal events."""

    id: Optional[int] = None
    event_type: EventType = EventType.NOTE
    event_date: date = field(default_factory=date.today)
    animal_id: Optional[int] = None  # For individual animal events
    mob_id: Optional[int] = None  # For mob-level events
    notes: str = ""
    recorded_by: str = ""
    created_at: Optional[datetime] = None


@dataclass
class MovementEvent:
    """A movement of animals between paddocks."""

    id: Optional[int] = None
    event_id: Optional[int] = None
    from_paddock_id: Optional[int] = None
    to_paddock_id: Optional[int] = None
    reason: str = ""  # e.g., "pasture low", "water issue", "rotation"
    head_count: int = 0  # Number of animals moved (for mob moves)


@dataclass
class TreatmentEvent:
    """A treatment administered to an animal or mob."""

    id: Optional[int] = None
    event_id: Optional[int] = None
    product_id: Optional[int] = None
    batch_number: str = ""
    dose: str = ""
    route: TreatmentRoute = TreatmentRoute.INJECTION_SC
    administered_by: str = ""
    meat_whp_end: Optional[date] = None  # Calculated meat WHP end date
    milk_whp_end: Optional[date] = None  # Calculated milk WHP end date
    esi_end: Optional[date] = None  # Calculated ESI end date


@dataclass
class WeighEvent:
    """A weight recording for an animal."""

    id: Optional[int] = None
    event_id: Optional[int] = None
    weight_kg: float = 0.0
    condition_score: Optional[float] = None  # Body condition score (1-5)


@dataclass
class Task:
    """A reminder or task generated from events."""

    id: Optional[int] = None
    title: str = ""
    description: str = ""
    due_date: Optional[date] = None
    source_event_id: Optional[int] = None  # Event that triggered this task
    animal_id: Optional[int] = None
    mob_id: Optional[int] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class PropertySettings:
    """Property-level settings and information."""

    id: Optional[int] = None
    property_name: str = ""
    pic: str = ""  # Primary Property Identification Code
    owner_name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
