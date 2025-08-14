from typing import Optional

from pydantic import BaseModel, field_validator

from openaas.metamodel.base import Identifier
from openaas.metamodel.reference import Reference


class AdministrativeInformation(BaseModel):
    """Informações administrativas de um Identifiable.

    Attributes:
        version: Versão (máx. 4 caracteres).
        revision: Revisão (máx. 4 caracteres; requer `version`).
        creator: Referência ao criador (global/model).
        templateId: Identificador do template ao qual esta instância está vinculada.
    """
    version: Optional[str] = None
    revision: Optional[str] = None
    creator: Optional[Reference] = None
    templateId: Optional[Identifier] = None

    @field_validator("revision")
    @classmethod
    def _revision_requires_version(cls, v, info):
        if v is not None and not info.data.get("version"):
            raise ValueError("revision requer version.")
        return v

    @field_validator("version")
    @classmethod
    def _maxlen_version(cls, v):
        if v is not None and len(v) > 4:
            raise ValueError("version deve ter no máximo 4 caracteres. (AASd-135)")
        return v

    @field_validator("revision")
    @classmethod
    def _maxlen_revision(cls, v):
        if v is not None and len(v) > 4:
            raise ValueError("revision deve ter no máximo 4 caracteres. (AASd-136)")
        return v