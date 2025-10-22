from django.urls import path
from .views import StringCreateView, StringDetailView, StringsListView, NaturalLanguageFilterView, StringListCreateView

urlpatterns = [
    path("strings/", StringListCreateView.as_view(), name="string-list-create"),
    path("strings/filter-by-natural-language", NaturalLanguageFilterView.as_view(), name="natlang_filter"),
    path("strings/<path:string_value>", StringDetailView.as_view(), name="detail_string"),
]
