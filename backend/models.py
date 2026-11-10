"""
Pydantic models for Cortex Loom events and analysis.
"""
import hashlib
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


def compute_event_id(label: str, year: float, whoWhat: Optional[str] = None) -> str:
    """Identifiant stable d'un événement (idempotence des upserts).

    Basé sur label + année + source, normalisés : le même événement
    (même label/année/source) produit toujours le même id, quelle que soit
    la valeur des autres champs (ex: stade de singularité réévalué).
    """
    key = f"{(label or '').strip().lower()}|{round(float(year), 2)}|{(whoWhat or '').strip().lower()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


class PharmakonAnalysis(BaseModel):
    """Pharmakon analysis model (v117+)"""
    s_curve_phase: int = Field(default=3, ge=1, le=5, description="Phase de la courbe en S (1-5)")
    remedy_percent: int = Field(default=50, ge=0, le=100, description="% Remède")
    poison_percent: int = Field(default=50, ge=0, le=100, description="% Poison")
    convergences: str = Field(default="Analyse simulée : N/A", description="Convergences avec d'autres domaines")
    grand_filter_analysis: str = Field(default="Analyse simulée : N/A", description="Analyse du Grand Filtre")
    final_note: str = Field(default="Note finale simulée.", description="Note finale (humour noir)")

    @classmethod
    def from_legacy(cls, data: Dict[str, Any]) -> "PharmakonAnalysis":
        """Convert legacy event data to PharmakonAnalysis"""
        return cls(
            s_curve_phase=data.get("s_curve_phase", 3),
            remedy_percent=data.get("pharmakon_remedy_percent", data.get("remedy_percent", 50)),
            poison_percent=data.get("pharmakon_poison_percent", data.get("poison_percent", 50)),
            convergences=data.get("convergences", "N/A"),
            grand_filter_analysis=data.get("grand_filter_analysis", "N/A"),
            final_note=data.get("final_note", "N/A")
        )


class Event(BaseModel):
    """Event model for Cortex Loom"""
    id: Optional[str] = Field(default=None, description="Identifiant stable (sha1 label+year+source)")
    year: float = Field(description="Année (ex: 2025.08)")
    value: int = Field(description="Valeur cumulative")
    label: str = Field(description="Titre de l'événement")
    category: str = Field(description="Catégorie (ex: '☢️ ENTROPIE')")
    whoWhat: str = Field(default="", description="Source/Auteur")
    description: str = Field(default="", description="Description détaillée")
    url: str = Field(default="", description="URL de référence")
    timestamp: Optional[str] = Field(default=None, description="Timestamp ISO")
    tipping: bool = Field(default=False, description="Point de bascule")
    analysis: Optional[PharmakonAnalysis] = Field(default=None, description="Analyse Pharmakon")

    @model_validator(mode="before")
    @classmethod
    def _lift_flat_analysis(cls, data):
        """Accepte les champs d'analyse aplatis à la racine (legacy ou nouveaux noms)."""
        if isinstance(data, dict) and "analysis" not in data:
            keys = ["s_curve_phase", "pharmakon_remedy_percent", "pharmakon_poison_percent",
                    "remedy_percent", "poison_percent", "convergences",
                    "grand_filter_analysis", "final_note"]
            sub = {k: data[k] for k in keys if k in data}
            if sub:
                if "pharmakon_remedy_percent" in sub:
                    sub["remedy_percent"] = sub.pop("pharmakon_remedy_percent")
                if "pharmakon_poison_percent" in sub:
                    sub["poison_percent"] = sub.pop("pharmakon_poison_percent")
                data = {k: v for k, v in data.items() if k not in keys}
                data["analysis"] = sub
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Convert a dictionary to Event, handling legacy formats.

        Accepte les deux conventions : champs d'analyse aplatis au niveau racine
        (legacy: pharmakon_remedy_percent / nouveau: remedy_percent) ou objet
        "analysis" imbriqué.
        """
        analysis_data: Dict[str, Any] = {}
        legacy_fields = ["s_curve_phase", "pharmakon_remedy_percent", "pharmakon_poison_percent",
                         "convergences", "grand_filter_analysis", "final_note"]
        new_fields = ["s_curve_phase", "remedy_percent", "poison_percent",
                      "convergences", "grand_filter_analysis", "final_note"]
        for field in legacy_fields + new_fields:
            if field in data:
                analysis_data[field] = data[field]
        if isinstance(data.get("analysis"), dict):
            analysis_data.update(data["analysis"])

        # Normalisation legacy -> noms actuels
        if "pharmakon_remedy_percent" in analysis_data:
            analysis_data["remedy_percent"] = analysis_data.pop("pharmakon_remedy_percent")
        if "pharmakon_poison_percent" in analysis_data:
            analysis_data["poison_percent"] = analysis_data.pop("pharmakon_poison_percent")
        # Cohérence remède/poison : la somme doit faire 100
        if "remedy_percent" in analysis_data and "poison_percent" not in analysis_data:
            analysis_data["poison_percent"] = 100 - int(analysis_data["remedy_percent"])
        if "poison_percent" in analysis_data and "remedy_percent" not in analysis_data:
            analysis_data["remedy_percent"] = 100 - int(analysis_data["poison_percent"])

        event_data = {k: v for k, v in data.items() if k not in (legacy_fields + new_fields) and k != "analysis"}

        # Champs legacy -> actuels
        if not event_data.get("description") and data.get("how"):
            event_data["description"] = data["how"]
        if not event_data.get("whoWhat") and data.get("author"):
            event_data["whoWhat"] = data["author"]

        analysis = None
        if analysis_data:
            analysis = PharmakonAnalysis(**analysis_data)

        ev = cls(**event_data, analysis=analysis)
        ev.ensure_id()
        return ev

    def to_dict(self) -> Dict[str, Any]:
        """Convert Event to dictionary (analysis aplatie + alias legacy pharmakon_*)"""
        result = self.model_dump(exclude={"analysis"})
        if self.analysis:
            a = self.analysis.model_dump()
            result.update(a)
            result["pharmakon_remedy_percent"] = a["remedy_percent"]
            result["pharmakon_poison_percent"] = a["poison_percent"]
        return result

    def ensure_id(self) -> str:
        """Calcule l'id stable si absent et le retourne."""
        if not self.id:
            self.id = compute_event_id(self.label, self.year, self.whoWhat)
        return self.id


class EventList(BaseModel):
    """List of events"""
    events: List[Event]
    count: int
    last_updated: Optional[str] = None
