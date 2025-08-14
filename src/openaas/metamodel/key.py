from pydantic import BaseModel, Field


class Key(BaseModel):
    """Par (tipo, valor) que compõe uma Reference.

    Attributes:
        type: Tipo do alvo referenciado por esta Key (ex.: 'Submodel', 'Property', 'File', 'Blob',
            'FragmentReference', 'GlobalReference', ...).
        value: Identificador do alvo (global para identifiables; idShort/nome ou índice para fragmentos).
            Em listas, um índice após 'SubmodelElementList' deve ser um número inteiro.
    """
    type: str = Field(..., description="Tipo do alvo (ex.: 'Submodel', 'Property', 'File').")
    value: str = Field(..., description="Identificador/valor associado a esta chave.")
