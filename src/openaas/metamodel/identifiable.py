from abc import ABC
from typing import Optional

from openaas.metamodel.administrative_information import AdministrativeInformation
from openaas.metamodel.base import Identifier
from openaas.metamodel.referable import Referable


class Identifiable(Referable, ABC):
    """Referable com ID global único.

    Attributes:
        id: Identificação global (IRI/IRDI/UUID).
        administration: Informações administrativas (opcional).
    """
    id: Identifier
    administration: Optional[AdministrativeInformation] = None