from models.company_synonym import SynonymGroup, SynonymGroupCreate, SynonymAddRequest


def test_synonym_group_model():
    group = SynonymGroup(group_id=1, names=["A", "B"])
    assert group.group_id == 1
    assert group.names == ["A", "B"]


def test_synonym_group_create_model():
    body = SynonymGroupCreate(names=["A", "B"])
    assert body.names == ["A", "B"]


def test_synonym_add_request_model():
    body = SynonymAddRequest(name="C")
    assert body.name == "C"
