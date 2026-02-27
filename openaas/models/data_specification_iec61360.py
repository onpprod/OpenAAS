"""AAS metamodel model class."""

from __future__ import annotations

from .data_specification_content import DataSpecificationContent
from typing import Literal


class DataSpecificationIec61360(DataSpecificationContent):
    """Model for DataSpecificationIec61360 in the AAS metamodel.

    Constraints:
    - Field set is aligned with definition `DataSpecificationIec61360` from aas.json.
    - Additional unknown fields are forbidden by AASBaseModel.
    """
    preferredName: list[LangStringPreferredNameTypeIec61360]
    shortName: list[LangStringShortNameTypeIec61360] | None = None
    unit: str | None = None
    unitId: Reference | None = None
    sourceOfDefinition: str | None = None
    symbol: str | None = None
    dataType: DataTypeIec61360 | None = None
    definition: list[LangStringDefinitionTypeIec61360] | None = None
    valueFormat: str | None = None
    valueList: ValueList | None = None
    value: str | None = None
    levelType: LevelType | None = None
    modelType: Literal['DataSpecificationIec61360'] = 'DataSpecificationIec61360'
