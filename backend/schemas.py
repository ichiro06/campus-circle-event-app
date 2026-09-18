from api.models import ApiModel
from api.models import to_camel as to_camel


class CircleRead(ApiModel):
    id: int
    name: str
    category: str
    official: bool
    activity_days: str
    place: str
    description: str
    tags: list[str]
    sns: str
    recruiting: bool


class EventRead(ApiModel):
    id: int
    title: str
    circle_name: str
    starts_at: str
    place: str
    type: str
    description: str
    tags: list[str]
