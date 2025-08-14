from abc import ABC
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from openaas.metamodel.reference import Reference


class HasSemantics(BaseModel, ABC):
    """Permite associar IDs semânticos ao elemento.

    Rules:
        - Se houver `supplementalSemanticId`, também deve haver `semanticId` (AASd-118).

    Attributes:
        semanticId: Referência ao conceito principal.
        supplementalSemanticId: Referências a conceitos suplementares.
    """
    semanticId: Optional[Reference] = None
    supplementalSemanticId: List[Reference] = Field(default_factory=list)

    @field_validator("supplementalSemanticId")
    @classmethod
    def _supp_requires_main(cls, v, info):
        if v and info.data.get("semanticId") is None:
            raise ValueError(
                "supplementalSemanticId requer semanticId (AASd-118)."
            )
        return v