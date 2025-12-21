"""API modules for USCardForum Discourse client.

Each module handles a specific domain of the Discourse API.
"""

from uscardforum.api.auth import AuthAPI
from uscardforum.api.base import BaseAPI
from uscardforum.api.categories import CategoriesAPI
from uscardforum.api.search import SearchAPI
from uscardforum.api.topics import TopicsAPI
from uscardforum.api.users import UsersAPI

__all__ = [
    "BaseAPI",
    "TopicsAPI",
    "UsersAPI",
    "SearchAPI",
    "CategoriesAPI",
    "AuthAPI",
]

