import pytest
from pydantic import ValidationError

from openaas.metamodel.asset_administration_shell import AssetAdministrationShell
from openaas.metamodel.asset_information import AssetInformation
from openaas.metamodel.reference import Reference
from openaas.metamodel.reference_type import ReferenceType

# Ajuste este import conforme teu metamodel
from openaas.metamodel.key import Key


def make_asset_info() -> AssetInformation:
    """
    Cria um AssetInformation mínimo para instanciar o AAS.
    Ajuste os campos conforme o teu AssetInformation real.
    """
    return AssetInformation(
        assetKind="Instance",
        globalAssetId="urn:uuid:11111111-1111-1111-1111-111111111111",
    )


def make_ref(first_key_type: str, ref_type: ReferenceType) -> Reference:
    """
    Helper para criar Reference com 1 key.
    """
    return Reference(
        type=ref_type,
        keys=[Key(type=first_key_type, value="urn:uuid:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")],
    )


# -------------------------
# derivedFrom validator
# -------------------------

def test_derived_from_none_is_ok():
    aas = AssetAdministrationShell(
        id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
        assetInformation=make_asset_info(),
        derivedFrom=None,
    )
    assert aas.derivedFrom is None


def test_derived_from_valid_model_reference_to_aas_ok():
    derived_from = make_ref("AssetAdministrationShell", ReferenceType.ModelReference)

    aas = AssetAdministrationShell(
        id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
        assetInformation=make_asset_info(),
        derivedFrom=derived_from,
    )

    assert aas.derivedFrom == derived_from


def test_derived_from_invalid_reference_type_raises():
    # Type errado (não ModelReference)
    derived_from = make_ref("GlobalReference", ReferenceType.ExternalReference)

    with pytest.raises(ValidationError) as exc:
        AssetAdministrationShell(
            id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
            assetInformation=make_asset_info(),
            derivedFrom=derived_from,
        )

    # Mensagem do teu ValueError precisa aparecer no ValidationError
    assert "derivedFrom deve referenciar um AssetAdministrationShell" in str(exc.value)


def test_derived_from_invalid_first_key_type_raises():
    # keys[0].type errado
    derived_from = make_ref("Submodel", ReferenceType.ModelReference)

    with pytest.raises(ValidationError) as exc:
        AssetAdministrationShell(
            id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
            assetInformation=make_asset_info(),
            derivedFrom=derived_from,
        )

    assert "derivedFrom deve referenciar um AssetAdministrationShell" in str(exc.value)


# -------------------------
# submodels validator
# -------------------------

def test_submodels_empty_list_is_ok():
    aas = AssetAdministrationShell(
        id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
        assetInformation=make_asset_info(),
        submodels=[],
    )
    assert aas.submodels == []


def test_submodels_all_valid_ok():
    sm1 = make_ref("Submodel", ReferenceType.ModelReference)
    sm2 = make_ref("Submodel", ReferenceType.ModelReference)

    aas = AssetAdministrationShell(
        id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
        assetInformation=make_asset_info(),
        submodels=[sm1, sm2],
    )

    assert aas.submodels == [sm1, sm2]


def test_submodels_invalid_reference_type_raises():
    sm1 = make_ref("GlobalReference", ReferenceType.ExternalReference)  # type errado

    with pytest.raises(ValidationError) as exc:
        AssetAdministrationShell(
            id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
            assetInformation=make_asset_info(),
            submodels=[sm1],
        )

    assert "Cada item em submodels deve referenciar um Submodel" in str(exc.value)


def test_submodels_invalid_first_key_type_raises():
    sm1 = make_ref("AssetAdministrationShell", ReferenceType.ModelReference)  # key[0].type errado

    with pytest.raises(ValidationError) as exc:
        AssetAdministrationShell(
            id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
            assetInformation=make_asset_info(),
            submodels=[sm1],
        )

    assert "Cada item em submodels deve referenciar um Submodel" in str(exc.value)


def test_submodels_mixed_valid_and_invalid_raises():
    ok = make_ref("Submodel", ReferenceType.ModelReference)
    bad = make_ref("GlobalReference", ReferenceType.ExternalReference)

    with pytest.raises(ValidationError) as exc:
        AssetAdministrationShell(
            id="urn:uuid:dddddddd-dddd-dddd-dddd-dddddddddddd",
            assetInformation=make_asset_info(),
            submodels=[ok, bad],
        )

    assert "Cada item em submodels deve referenciar um Submodel" in str(exc.value)
