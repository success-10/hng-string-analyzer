from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound
from .models import AnalyzedString, compute_sha256
from .serializers import AnalyzedStringSerializer, CreateAnalyzeSerializer
from .filters import AnalyzedStringFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from .natlang import parse_natural_language_query
from django.db import IntegrityError

# Create your views here.

class StringListCreateView(APIView):
    """
    Handles:
      - POST /strings: create new analyzed string
      - GET /strings: list or filter analyzed strings
    """

    def get(self, request):
        queryset = AnalyzedString.objects.all()
        filterset = AnalyzedStringFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response({"detail": "Invalid query parameters", "errors": filterset.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        filtered_qs = filterset.qs
        serializer = AnalyzedStringSerializer(filtered_qs, many=True)

        # Collect filters applied
        filters_applied = {}
        for k in ["is_palindrome", "min_length", "max_length", "word_count", "contains_character"]:
            v = request.query_params.get(k)
            if v is not None:
                if k == "is_palindrome":
                    filters_applied[k] = v.lower() == "true"
                elif k in ("min_length", "max_length", "word_count"):
                    try:
                        filters_applied[k] = int(v)
                    except ValueError:
                        return Response({"detail": "Invalid query parameter type"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    filters_applied[k] = v

        data = {
            "count": filtered_qs.count(),
            "filters_applied": filters_applied,
            "results": serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateAnalyzeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid request", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        value = serializer.validated_data["value"]
        if not isinstance(value, str):
            return Response(
                {"detail": "Invalid data type for 'value' (must be string)"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        hash_id = compute_sha256(value)
        if AnalyzedString.objects.filter(id=hash_id).exists():
            return Response(
                {"detail": "String already exists in the system"},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            obj = AnalyzedString(value=value)
            obj.save()
        except IntegrityError:
            return Response(
                {"detail": "String already exists in the system"},
                status=status.HTTP_409_CONFLICT,
            )

        ser = AnalyzedStringSerializer(obj)
        return Response(ser.data, status=status.HTTP_201_CREATED)


# 1. POST /strings
class StringCreateView(APIView):
    def post(self, request):
        serializer = CreateAnalyzeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid request", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        value = serializer.validated_data["value"]
        if not isinstance(value, str):
            return Response({"detail": "Invalid data type for 'value' (must be string)"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        hash_id = compute_sha256(value)
        if AnalyzedString.objects.filter(id=hash_id).exists():
            return Response({"detail": "String already exists in the system"}, status=status.HTTP_409_CONFLICT)
        try:
            obj = AnalyzedString(value=value)
            obj.save()
        except IntegrityError:
            return Response({"detail": "String already exists in the system"}, status=status.HTTP_409_CONFLICT)
        ser = AnalyzedStringSerializer(obj)
        return Response(ser.data, status=status.HTTP_201_CREATED)

# 2. GET /strings/{string_value}
class StringDetailView(APIView):
    def get_object_by_value_or_hash(self, string_value):
        # Try to get by exact string value first
        obj = AnalyzedString.objects.filter(value=string_value).first()
        if obj:
            return obj

        # Try to get by SHA256 hash 
        obj = AnalyzedString.objects.filter(id=string_value).first()
        if obj:
            return obj

        # Return None if not found
        return None

    def get(self, request, string_value):
        obj = self.get_object_by_value_or_hash(string_value)
        if not obj:
            return Response(
                {"detail": "String does not exist in the system."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AnalyzedStringSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, string_value):
        obj = self.get_object_by_value_or_hash(string_value)
        if not obj:
            return Response(
                {"detail": "String does not exist in the system."},
                status=status.HTTP_404_NOT_FOUND
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# 3. GET /strings with filtering
class StringsListView(generics.ListAPIView):
    serializer_class = AnalyzedStringSerializer
    queryset = AnalyzedString.objects.all()
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = AnalyzedStringFilter
    ordering_fields = ["created_at", "length"]

    def list(self, request, *args, **kwargs):
        # Validate query params types
        try:
            return super().list(request, *args, **kwargs)
        except ValueError as e:
            return Response({"detail": "Invalid query parameter values or types", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        # Add filters_applied in response
        filters_applied = {}
        for k in ["is_palindrome", "min_length", "max_length", "word_count", "contains_character"]:
            v = request.query_params.get(k)
            if v is not None:
                # coerce booleans/ints for readability
                if k == "is_palindrome":
                    filters_applied[k] = v.lower() == "true"
                elif k in ("min_length", "max_length", "word_count"):
                    try:
                        filters_applied[k] = int(v)
                    except ValueError:
                        return Response({"detail": "Invalid query parameter values or types"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    filters_applied[k] = v
        data = {
            "data": resp.data,
            "count": self.get_queryset().count() if not hasattr(resp, "data") else len(resp.data),
            "filters_applied": filters_applied,
        }
        return Response(data)

# 4. Natural Language filtering: GET /strings/filter-by-natural-language?query=...
class NaturalLanguageFilterView(APIView):
    def get(self, request):
        q = request.query_params.get("query")
        if not q:
            return Response({"detail": "query parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            parsed = parse_natural_language_query(q)
        except ValueError as e:
            return Response({"detail": "Unable to parse natural language query"}, status=status.HTTP_400_BAD_REQUEST)

        # detect conflicting filters (example)
        if "min_length" in parsed and "max_length" in parsed and parsed["min_length"] > parsed["max_length"]:
            return Response({"detail": "Query parsed but resulted in conflicting filters"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Build queryset
        qs = AnalyzedString.objects.all()
        if parsed.get("is_palindrome") is True:
            qs = qs.filter(is_palindrome=True)
        if "word_count" in parsed:
            qs = qs.filter(word_count=parsed["word_count"])
        if "min_length" in parsed:
            qs = qs.filter(length__gte=parsed["min_length"])
        if "max_length" in parsed:
            qs = qs.filter(length__lte=parsed["max_length"])
        if "contains_character" in parsed:
            ch = parsed["contains_character"]
            if not isinstance(ch, str) or len(ch) != 1:
                return Response({"detail": "Unable to parse natural language query (contains_character must be single char)"}, status=status.HTTP_400_BAD_REQUEST)
            # prefer JSON key lookup if DB supports; otherwise fallback to value contains
            qs = qs.filter(value__contains=ch)

        serializer = AnalyzedStringSerializer(qs, many=True)
        return Response({
            "data": serializer.data,
            "count": qs.count(),
            "interpreted_query": {
                "original": q,
                "parsed_filters": parsed
            }
        })
