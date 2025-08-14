from openaas.metamodel.qualifier import Qualifier, Reference
from openaas.metamodel.reference import ReferenceType, Key


def test_qualifier_with_value_or_valueid():
    q1 = Qualifier(type="tol", valueType="double", value="0.1")
    assert q1.value == "0.1"

    q2 = Qualifier(
        type="unit",
        valueId=Reference(
            type=ReferenceType.ExternalReference,
            keys=[Key(type="GlobalReference", value="0173-1#05-AAA650#002")]
        )
    )
    assert q2.valueId is not None
