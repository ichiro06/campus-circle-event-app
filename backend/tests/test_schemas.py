import pytest

from schemas import to_camel


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("id", "id"),
        ("activity_days", "activityDays"),
        ("circle_manager_membership", "circleManagerMembership"),
    ],
)
def test_to_camel(source: str, expected: str) -> None:
    assert to_camel(source) == expected
