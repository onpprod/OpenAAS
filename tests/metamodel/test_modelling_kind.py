from openaas.metamodel.modelling_kind import ModellingKind


def test_modelling_kind_values():
    assert ModellingKind.Instance.value == "Instance"
    assert ModellingKind.Template.value == "Template"
