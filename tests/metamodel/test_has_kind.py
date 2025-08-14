from openaas.metamodel.has_kind import HasKind, ModellingKind


class _K(HasKind):
    pass

def test_has_kind_default_instance():
    x = _K()
    assert x.kind == ModellingKind.Instance

def test_has_kind_template():
    x = _K(kind=ModellingKind.Template)
    assert x.kind == ModellingKind.Template
