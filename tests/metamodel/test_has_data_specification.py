from openaas.metamodel.has_data_specification import HasDataSpecification, Reference
from openaas.metamodel.reference_type import ReferenceType
from openaas.metamodel.key import Key


class _D(HasDataSpecification):
    pass

def test_has_data_spec_default_list():
    d = _D()
    assert d.dataSpecification == []

def test_has_data_spec_with_item():
    d = _D(
        dataSpecification=[
            Reference(type=ReferenceType.ExternalReference,
                      keys=[Key(type="GlobalReference", value="IEC61360")])
        ]
    )
    assert len(d.dataSpecification) == 1
