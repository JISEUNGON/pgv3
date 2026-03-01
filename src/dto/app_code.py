from __future__ import annotations

from enum import Enum
from typing import Optional


class AppCode(str, Enum):
    DATA_IMPORTER = "DATA_IMPORTER"
    PGV2 = "PGV2"
    ANLS_PROJECT = "ANLS_PROJECT"
    ANLS_TEMPLATE_EDA = "ANLS_TEMPLATE_EDA"
    ANLS_TEMPLATE_NATURAL = "ANLS_TEMPLATE_NATURAL"
    ANLS_TEMPLATE_SPACE_MARKER = "ANLS_TEMPLATE_SPACE_MARKER"
    ANLS_TEMPLATE_SPACE_POLYGON = "ANLS_TEMPLATE_SPACE_POLYGON"
    ANLS_TEMPLATE_SPACE_BUBBLE = "ANLS_TEMPLATE_SPACE_BUBBLE"
    ANLS_TEMPLATE_SPACE_HEATMAP = "ANLS_TEMPLATE_SPACE_HEATMAP"

    @classmethod
    def find(cls, value: Optional[str]) -> Optional["AppCode"]:
        if value is None:
            return None
        for code in cls:
            if code.value.lower() == value.lower():
                return code
        return None

