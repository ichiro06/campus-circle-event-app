from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


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
