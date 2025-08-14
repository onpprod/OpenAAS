from openaas.metamodel.data_element import DataElement


class _DE(DataElement):
    pass

def test_data_element_constructs():
    d = _DE(idShort="valueA")
    assert d.idShort == "valueA"
