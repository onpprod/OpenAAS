from openaas.metamodel.has_extensions import HasExtensions, Extension


class _X(HasExtensions):
    pass

def test_has_extensions_default_list():
    x = _X()
    assert x.extension == []

def test_has_extensions_add_extension():
    ext = Extension(name="customFlag")
    x = _X(extension=[ext])
    assert x.extension[0].name == "customFlag"
