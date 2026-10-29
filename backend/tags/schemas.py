from uuid import UUID

from api.models import ApiModel, CollectionResponse
from api.pagination import PaginationParams


class TagListQuery(PaginationParams):
    """The public tag catalog accepts cursor pagination only; it has no filters."""


class TagCatalogItem(ApiModel):
    id: UUID
    name: str
    slug: str


# Standard collection envelope; deliberately without the Circle list's ``totalCount``.
class TagCollectionResponse(CollectionResponse[TagCatalogItem]):
    pass
