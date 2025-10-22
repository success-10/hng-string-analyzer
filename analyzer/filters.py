from django_filters import rest_framework as filters
from django.db import models
from django.core.exceptions import ValidationError
from .models import AnalyzedString
from django.db import connection
from django.db.models import Q
class AnalyzedStringFilter(filters.FilterSet):
    """
    FilterSet for AnalyzedString.

    Query params supported:
      - is_palindrome (true/false)
      - min_length (int)
      - max_length (int)
      - word_count (int)
      - contains_character (single char)  <- validated
    """
    is_palindrome = filters.BooleanFilter(field_name="is_palindrome")
    min_length = filters.NumberFilter(field_name="length", lookup_expr="gte")
    max_length = filters.NumberFilter(field_name="length", lookup_expr="lte")
    word_count = filters.NumberFilter(field_name="word_count", lookup_expr="exact")
    contains_character = filters.CharFilter(method="filter_contains_char")

    class Meta:
        model = AnalyzedString
        fields = ["is_palindrome", "min_length", "max_length", "word_count", "contains_character"]

    def filter_contains_char(self, queryset, name, value):
        """
        Filter for a single character contained in the character_frequency_map.

        Behavior:
          - If value is not a single character, raise ValueError (caught by view -> 400).
          - Prefer JSON key lookup when supported by the DB/Django.
          - Fall back to searching the `value` text (less precise / slower) if JSON lookup is not available.
        """
        # Validate input: must be a single character
        if value is None:
            raise ValueError("contains_character parameter is required")
        value = str(value)
        if len(value) != 1:
            raise ValueError("contains_character must be a single character")

        ch = value

        # Detect JSONField on model
        field = queryset.model._meta.get_field("character_frequency_map")
        is_json_field = field.get_internal_type() in ("JSONField", "JSONBField")

        # Try DB-backed JSON key lookup if possible
        if is_json_field:
            # For Postgres and modern Django, has_key lookup is supported:
            try:
                return queryset.filter(character_frequency_map__has_key=ch)
            except Exception:
                # fallback to other approaches below
                pass

        # If JSON lookups aren't supported for your DB, fallback to searching the raw value.
        # This is less precise — it checks whether the original string contains the char.
        # Document this behaviour in README.
        return queryset.filter(value__contains=ch)