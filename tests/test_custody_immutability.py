from app.repositories import custody_event_repository


def test_custody_event_repository_exposes_no_update_or_delete():
    exported_names = {name for name in dir(custody_event_repository) if not name.startswith("_")}

    assert "create_custody_event" in exported_names
    assert "list_by_evidence_item" in exported_names
    assert not any(name.startswith("update") for name in exported_names)
    assert not any(name.startswith("delete") for name in exported_names)
