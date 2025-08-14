from openaas.metamodel.submodel_element import SubmodelElement


# SME é abstrata; criamos um stub concreto mínimo:
class _SME(SubmodelElement):
    pass

def test_submodel_element_constructs():
    s = _SME(idShort="p1")
    assert s.idShort == "p1"
