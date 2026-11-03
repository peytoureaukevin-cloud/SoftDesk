"""Pagination commune aux listes de l'API SoftDesk."""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Limite les réponses tout en autorisant une taille de page plafonnée."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
