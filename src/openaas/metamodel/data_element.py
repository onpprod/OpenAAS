from abc import ABC

from openaas.metamodel.submodel_element import SubmodelElement


class DataElement(SubmodelElement, ABC):
    """Abstração de SME com 'valor' (ex.: Property, Range, File)."""
    pass