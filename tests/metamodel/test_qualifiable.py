from openaas.metamodel.qualifiable import Qualifiable, Qualifier


class _Q(Qualifiable):
    pass

def test_qualifiable_default_list():
    x = _Q()
    assert x.qualifier == []

def test_qualifiable_add_qualifier():
    x = _Q(qualifier=[Qualifier(type="acc", valueType="percent", value="95")])
    assert x.qualifier and x.qualifier[0].type == "acc"
