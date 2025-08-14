from openaas.metamodel.referable import Referable


class _Ref(Referable):
    pass

def test_referable_fields_optional():
    r = _Ref(idShort="Name", displayName={"en": "Name"}, description={"en": "Desc"})
    assert r.idShort == "Name"
    assert r.displayName["en"] == "Name"
    assert r.description["en"] == "Desc"
