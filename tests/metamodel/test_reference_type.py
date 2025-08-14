import pytest
from openaas.metamodel.reference_type import ReferenceType


def test_reference_type_values():
    assert ReferenceType.ModelReference.value == "ModelReference"
    assert ReferenceType.ExternalReference.value == "ExternalReference"
