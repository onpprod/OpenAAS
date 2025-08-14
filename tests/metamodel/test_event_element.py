from openaas.metamodel.event_element import EventElement


class _EE(EventElement):
    pass

def test_event_element_constructs():
    e = _EE(idShort="evt")
    assert e.idShort == "evt"
