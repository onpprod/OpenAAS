from pydantic import BaseModel, Field, field_validator
from typing import List, ClassVar

from openaas.metamodel.key import Key
from openaas.metamodel.reference_type import ReferenceType


class Reference(BaseModel):
    """Cadeia de keys que referencia um alvo global ou de modelo.

    Rules:
        - O 1º Key depende de `type`:
            * ModelReference → 1º ∈ {'AssetAdministrationShell','Submodel','ConceptDescription'}
            * ExternalReference → 1º ∈ {'GlobalReference'}
        - Se houver >1 Key:
            * Todas as seguintes devem ser 'fragment keys' (SMEs, arquivos, fragmentos).
            * 'FragmentReference' só é permitido como **último** e deve ser precedido de 'File' ou 'Blob'.
            * Se uma Key anterior for 'SubmodelElementList', a **próxima** Key.value deve ser um inteiro.

        Estas regras estão alinhadas ao Part 1 (V3.x) – ver AASd-121..128.
    """

    type: ReferenceType = Field(
        ...,
        description="ModelReference (AAS/Submodel/CD/SME) ou ExternalReference (global)."
    )
    keys: List[Key] = Field(
        ...,
        description="Cadeia de keys (1..n) descrevendo o caminho até o alvo."
    )

    # Conjuntos de tipos usados nas validações (recorte suficiente para o dia-a-dia)
    _AAS_IDENTIFIABLES: ClassVar[set[str]] = {"AssetAdministrationShell", "Submodel", "ConceptDescription"}
    _GENERIC_GLOBALLY_IDENTIFIABLES: ClassVar[set[str]] = {"GlobalReference"}  # recorte mínimo seguro
    _FRAGMENT_KEYS: ClassVar[set[str]] = {
        # SubmodelElement (supertipo) e subtipos comuns
        "SubmodelElement", "Property", "MultiLanguageProperty", "Range",
        "ReferenceElement", "RelationshipElement", "AnnotatedRelationshipElement",
        "SubmodelElementCollection", "SubmodelElementList",
        "File", "Blob",
        "Entity",
        "BasicEventElement", "Operation",
        # marcador de fragmento (ex.: parte de arquivo)
        "FragmentReference",
    }
    _GENERIC_FRAGMENT_KEYS: ClassVar[set[str]] = {"FragmentReference"}

    @field_validator("keys")
    @classmethod
    def _validate_keys_chain(cls, keys: List[Key], info):
        if not keys:
            raise ValueError("Reference/keys deve conter pelo menos 1 item.")

        ref_type: ReferenceType = info.data.get("type")
        first_type = keys[0].type

        # AASd-123 (ModelReference) e AASd-122 (ExternalReference – 1ª key global)
        if ref_type == ReferenceType.ModelReference:
            if first_type not in cls._AAS_IDENTIFIABLES:
                raise ValueError("Para ModelReference, o primeiro Key.type deve ser um dos "
                                 f"{sorted(cls._AAS_IDENTIFIABLES)}. (AASd-123)")
        elif ref_type == ReferenceType.ExternalReference:
            if first_type not in cls._GENERIC_GLOBALLY_IDENTIFIABLES:
                raise ValueError("Para ExternalReference, o primeiro Key.type deve ser "
                                 "'GlobalReference'. (AASd-122)")

        if len(keys) > 1:
            if ref_type == ReferenceType.ModelReference:
                # AASd-125: após a 1ª, só FragmentKeys
                for k in keys[1:]:
                    if k.type not in cls._FRAGMENT_KEYS:
                        raise ValueError("Em ModelReference com múltiplas keys, todas após a primeira "
                                         f"devem ser fragment keys. Encontrado '{k.type}'. (AASd-125)")

                # AASd-126/127: FragmentReference só no fim e após File/Blob
                frag_positions = [i for i, k in enumerate(keys) if k.type in cls._GENERIC_FRAGMENT_KEYS]
                if frag_positions:
                    if frag_positions[-1] != len(keys) - 1:
                        raise ValueError("FragmentReference só é permitido como última key. (AASd-126)")
                    if len(keys) < 2 or keys[-2].type not in {"File", "Blob"}:
                        raise ValueError("FragmentReference deve ser precedido por 'File' ou 'Blob'. (AASd-127)")

                # AASd-128: índice inteiro após SubmodelElementList
                for i in range(len(keys) - 1):
                    if keys[i].type == "SubmodelElementList":
                        if not keys[i + 1].value.isdigit():
                            raise ValueError("Após 'SubmodelElementList', o próximo Key.value deve ser "
                                             "um inteiro (posição). (AASd-128)")

            elif ref_type == ReferenceType.ExternalReference:
                # AASd-124: a última key deve ser GlobalReference OU FragmentReference
                last_type = keys[-1].type
                if last_type not in (cls._GENERIC_GLOBALLY_IDENTIFIABLES | cls._GENERIC_FRAGMENT_KEYS):
                    raise ValueError("Em ExternalReference, a última key deve ser GlobalReference "
                                     "ou FragmentReference. (AASd-124)")

        return keys
