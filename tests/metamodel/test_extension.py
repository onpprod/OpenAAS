import pytest
from pydantic import ValidationError

# conforme seus exemplos de import
from openaas.metamodel.extension import Extension, Reference
from openaas.metamodel.reference import ReferenceType, Key


def test_extension_minimal():
    e = Extension(name="x-opt")
    assert e.name == "x-opt"
    assert e.value is None
    assert e.semanticId is None


# -------------------------
# AASd-123: ModelReference
# -------------------------

def test_modelreference_first_key_must_be_identifiable_ok():
    r = Reference(
        type=ReferenceType.ModelReference,
        keys=[Key(type="Submodel", value="urn:sm")]
    )
    assert r.keys[0].type == "Submodel"


def test_modelreference_first_key_must_be_identifiable_invalid():
    with pytest.raises(ValidationError):
        Reference(
            type=ReferenceType.ModelReference,
            keys=[Key(type="Property", value="P")]
        )


# -------------------------------------------------------------
# AASd-125: Keys após a primeira devem ser FragmentKeys
# -------------------------------------------------------------

def test_modelreference_following_keys_must_be_fragment_invalid():
    with pytest.raises(ValidationError):
        Reference(
            type=ReferenceType.ModelReference,
            keys=[
                Key(type="Submodel", value="urn:sm"),
                Key(type="ConceptDescription", value="urn:cd"),  # não é fragment key
            ]
        )


# --------------------------------------------------------------------
# AASd-126/127: FragmentReference só no fim e precedido de File/Blob
# --------------------------------------------------------------------

def test_fragmentreference_must_be_last_invalid():
    with pytest.raises(ValidationError):
        Reference(
            type=ReferenceType.ModelReference,
            keys=[
                Key(type="Submodel", value="urn:sm"),
                Key(type="File", value="manual.pdf"),
                Key(type="FragmentReference", value="/page/1"),
                Key(type="Property", value="Title"),  # algo depois do fragment → inválido
            ]
        )


def test_fragmentreference_must_be_preceded_by_file_or_blob_invalid():
    with pytest.raises(ValidationError):
        Reference(
            type=ReferenceType.ModelReference,
            keys=[
                Key(type="Submodel", value="urn:sm"),
                Key(type="Property", value="P"),
                Key(type="FragmentReference", value="#frag"),  # não precedido por File/Blob
            ]
        )


# -----------------------------------------------------------------
# AASd-128: índice inteiro após SubmodelElementList
# -----------------------------------------------------------------

def test_submodelelementlist_with_int_index_ok():
    r = Reference(
        type=ReferenceType.ModelReference,
        keys=[
            Key(type="Submodel", value="urn:sm"),
            Key(type="SubmodelElementList", value="Items"),
            # logo após a lista, um índice (valor numérico); o tipo deve ser fragment key
            Key(type="SubmodelElement", value="5"),
        ]
    )
    assert r.keys[2].value == "5"


def test_submodelelementlist_index_must_be_int_invalid():
    with pytest.raises(ValidationError):
        Reference(
            type=ReferenceType.ModelReference,
            keys=[
                Key(type="Submodel", value="urn:sm"),
                Key(type="SubmodelElementList", value="Items"),
                Key(type="SubmodelElement", value="five"),  # precisa ser inteiro
            ]
        )


# ----------------------------------------
# ExternalReference (AASd-122, AASd-126)
# ----------------------------------------

def test_externalreference_first_key_global_ok():
    r = Reference(
        type=ReferenceType.ExternalReference,
        keys=[Key(type="GlobalReference", value="0173-1#02-BAA120#008")]
    )
    assert r.keys[0].type == "GlobalReference"


def test_externalreference_wrong_first_key_invalid():
    with pytest.raises(ValidationError):
        Reference(
            type=ReferenceType.ExternalReference,
            keys=[Key(type="Submodel", value="urn:x")]
        )


def test_externalreference_last_may_be_fragment_ok():
    r = Reference(
        type=ReferenceType.ExternalReference,
        keys=[
            Key(type="GlobalReference", value="https://example.com/spec.pdf"),
            Key(type="FragmentReference", value="#chapter-2"),
        ]
    )
    assert r.keys[-1].type == "FragmentReference"


