# tests/metamodel/test_has_semantics.py
import pytest
from pydantic import ValidationError

from openaas.metamodel.has_semantics import HasSemantics, Reference
from openaas.metamodel.reference_type import ReferenceType
from openaas.metamodel.key import Key


class _S(HasSemantics):
    """Stub concreto para testar o mixin HasSemantics."""
    pass


def _ext_ref(val: str) -> Reference:
    """Atalho para ExternalReference mínima (1ª key GlobalReference)."""
    return Reference(
        type=ReferenceType.ExternalReference,
        keys=[Key(type="GlobalReference", value=val)],
    )


def test_has_semantics_ok_with_semantic_id():
    # cobre: v = [], semanticId != None (ramo 'if v' = False)
    s = _S(semanticId=_ext_ref("0173-1#02-BAA120#008"))
    assert s.semanticId is not None
    assert s.supplementalSemanticId == []


def test_has_semantics_supplemental_requires_main_error():
    # cobre: v != [], semanticId = None -> levanta erro (ramo True)
    with pytest.raises(ValidationError) as exc:
        _S(supplementalSemanticId=[_ext_ref("X")])
    msg = str(exc.value)
    assert "supplementalSemanticId requer semanticId" in msg


def test_has_semantics_supplemental_with_main_ok():
    # cobre: v != [], semanticId != None -> OK (ramo True mas sem erro)
    s = _S(
        semanticId=_ext_ref("0173-1#02-BAA120#008"),
        supplementalSemanticId=[_ext_ref("0173-1#02-BAF577#002"), _ext_ref("https://example.com/concept")],
    )
    assert len(s.supplementalSemanticId) == 2


def test_has_semantics_default_list_is_empty():
    # cobre: criação com defaults (lista vem vazia por default_factory=list)
    s = _S()
    assert s.supplementalSemanticId == []
    assert s.semanticId is None


def test_has_semantics_explicit_empty_list_ok():
    # cobre: v = [] explícito com semanticId ausente (ramo 'if v' = False)
    s = _S(supplementalSemanticId=[])
    assert s.supplementalSemanticId == []
    assert s.semanticId is None

