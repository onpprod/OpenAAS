import pytest
from pydantic import ValidationError
from openaas.metamodel.identifiable import Identifiable

class _I(Identifiable):
    pass

def test_identifiable_ok():
    i = _I(id="urn:example:aas:1")
    assert i.id == "urn:example:aas:1"

def test_identifiable_requires_id():
    with pytest.raises(ValidationError):
        _I()  # id é obrigatório
