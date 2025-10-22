from rest_framework import serializers
from .models import AnalyzedString

class AnalyzedStringPropertiesSerializer(serializers.Serializer):
    length = serializers.IntegerField()
    is_palindrome = serializers.BooleanField()
    unique_characters = serializers.IntegerField()
    word_count = serializers.IntegerField()
    sha256_hash = serializers.CharField()
    character_frequency_map = serializers.DictField(child=serializers.IntegerField())
    

class AnalyzedStringSerializer(serializers.ModelSerializer):
    """
    Serializer for AnalyzedString model used in responses.
    'properties' is constructed from model fields for a compact output.
    """

    properties = serializers.SerializerMethodField()
    id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)


    class Meta:
        model = AnalyzedString
        fields = ["id", "value", "properties", "created_at"]
        read_only_fields = ["id", "properties", "created_at"]

    def get_properties(self, obj):
        return {
            "length": obj.length,
            "is_palindrome": obj.is_palindrome,
            "unique_characters": obj.unique_characters,
            "word_count": obj.word_count,
            "sha256_hash": obj.id,
            "character_frequency_map": obj.character_frequency_map,
        }

class CreateAnalyzeSerializer(serializers.Serializer):
    """
    Input serializer for POST /strings.
    - trims whitespace
    - enforces non-empty string
    - optional max_length to prevent abuse
    """
    value = serializers.CharField()

    def validate_value(self, v: str) -> str:
        if not isinstance(v, str):
            raise serializers.ValidationError("value must be a string")
        # trim whitespace so " hello " == "hello"
        v = v.strip()

        # reject empty/whitespace-only inputs per spec
        if not v:
            raise serializers.ValidationError("The 'value' field cannot be empty.")

        # (Optional) further validation: disallow newline-only, control chars, etc.
        # e.g. if you want to forbid strings with only control chars:
        # if all(ord(ch) < 32 for ch in v): raise ...

        return v
