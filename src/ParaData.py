from __future__ import annotations

import json
import re
import typing
from dataclasses import asdict, dataclass, field, fields, is_dataclass


# Torsions Test Stand Settings
@dataclass
class Setup:
    force_scale: float = 1.0  # Skalierungsfaktor für Kraftmessung
    daq_ch_force: str = "Dev1/ai0"  # NIDAQmx Kanal für Kraftmessung
    distance_scale: float = 1.0  # Skalierungsfaktor für Distanzmessung
    daq_ch_distance: str = "Dev1/ai1"  # NIDAQmx Kanal für Distanzmessung
    interval: int = 1  # Messintervall in Sekunden
    sample_name: str = "Sample"  # Name der Probe
    start_path: str = ""  # Startverzeichnis für die Messung


# HauptParameterclass
@dataclass
class Parameter:
    Setup: Setup = field(default_factory=Setup)


param: Parameter = None


def load_param(filepath: str) -> Parameter:
    def from_dict(cls, data):
        # Listen
        if isinstance(data, list):
            # Prüfe, ob cls ein generischer Typ ist
            if hasattr(cls, "__origin__") and cls.__origin__ in (list, typing.List):
                item_type = cls.__args__[0]
                return [from_dict(item_type, item) for item in data]
            else:
                return data  # Standardliste mit einfachen Typen
        # Dictionaries
        elif isinstance(data, dict):
            if hasattr(cls, "__dataclass_fields__"):
                field_types = {f.name: f.type for f in fields(cls)}
                resolved_types = {}
                for key, field_type in field_types.items():
                    if isinstance(field_type, str):
                        resolved_types[key] = eval(field_type)
                    else:
                        resolved_types[key] = field_type
                return cls(**{key: from_dict(resolved_types[key], value) for key, value in data.items()})
            else:
                return data
        else:
            return data

    with open(filepath) as file:
        data = json.load(file)  # Lade JSON-Datei

    # Konvertiere Dictionary in Parameter-Dataclass
    return from_dict(Parameter, data)


def save_param(param: Parameter, filepath: str):
    def to_dict(obj):
        if isinstance(obj, list):
            return [to_dict(item) for item in obj]
        elif hasattr(obj, "__dict__"):
            return {key: to_dict(value) for key, value in obj.__dict__.items()}
        else:
            return obj

    with open(filepath, "w") as file:
        json_str = json.dumps(to_dict(param), indent=4, ensure_ascii=False)
        # Listen (z.B. Setpoints) kompakt machen
        json_str = re.sub(r"\[\s+([^\[\]]+?)\s+\]", lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", json_str)
        file.write(json_str)


def init_param(filepath: str = None):
    global param
    if filepath is None:
        param = Parameter()  # Verwendet automatisch die Standardwerte aus den Dataclasses
    else:
        param = load_param(filepath)


def save_current_param(filepath: str):
    if param is None:
        raise ValueError("Parameter Instanz wurde nicht initialisiert!")
    save_param(param, filepath)


def flatten_param(param, parent_key="", sep="_"):
    """
    Rekursive Funktion, um eine verschachtelte Dataclass in ein flaches Dictionary umzuwandeln.
    """
    if is_dataclass(param):
        param = asdict(param)  # Falls es eine Dataclass ist, in ein Dictionary umwandeln
    items = []
    for k, v in param.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_param(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Falls die Liste numerische Werte enthält, speichern wir sie als Zeichenkette
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


parameter_units = {
    # Temperature Settings
    "Setup.force_scale": "N",
    "Setup.distance_scale": "mm",
    "Setup.interval": "s",
}
