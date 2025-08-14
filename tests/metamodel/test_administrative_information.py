import pytest
from pydantic import ValidationError
from openaas.metamodel.administrative_information import AdministrativeInformation


def test_admin_info_ok():
    a = AdministrativeInformation(version="1", revision="0")
    assert a.version == "1"
    assert a.revision == "0"

def test_admin_info_revision_requires_version():
    with pytest.raises(ValidationError):
        AdministrativeInformation(revision="1")  # sem version

def test_admin_info_version_len_max_4():
    with pytest.raises(ValidationError):
        AdministrativeInformation(version="12345")

def test_admin_info_revision_len_max_4():
    with pytest.raises(ValidationError):
        AdministrativeInformation(version="1", revision="12345")
