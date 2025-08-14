from abc import ABC
from typing import Optional

from pydantic import BaseModel

from openaas.metamodel.modelling_kind import ModellingKind


class HasKind(BaseModel, ABC):
    """Distingue Template vs Instance.

    Attributes:
        kind: Tipo do elemento (default: Instance).
    """
    kind: Optional[ModellingKind] = ModellingKind.Instance