from src.data_sources.fixtures import load_fixture_jobs


def test_fixture_dataset_has_week1_target_size() -> None:
    fixtures = load_fixture_jobs()

    assert 40 <= len(fixtures) <= 60
    assert len({item.id for item in fixtures}) == len(fixtures)
