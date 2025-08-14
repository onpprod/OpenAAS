import pytest
from pydantic import ValidationError
from openaas.metamodel.key import Key

def test_key_ok():
    k = Key(type="Submodel", value="urn:example:submodel:1")
    assert k.type == "Submodel"
    assert k.value == "urn:example:submodel:1"

def test_key_missing_fields():
    with pytest.raises(ValidationError):
        Key()  # type e value obrigatórios
