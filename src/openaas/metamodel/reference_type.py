from enum import Enum


class ReferenceType(str, Enum):
    """Tipo de referência.

    - ExternalReference: referência global/externa (p.ex., IRDI/IRI).
    - ModelReference: referência a elementos do modelo AAS (AAS/Submodel/CD/SME).

    As regras para o 1º Key e a cadeia de Keys dependem deste tipo.
    """
    ExternalReference = "ExternalReference"
    ModelReference = "ModelReference"