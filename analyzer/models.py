from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import hashlib


# Utility: compute SHA-256 hash of the string
def compute_sha256(text: str) -> str:
    """Compute and return the SHA-256 hash of a given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AnalyzedString(models.Model):
    # Using sha256 as the primary key
    id = models.CharField(max_length=64, primary_key=True, editable=False)
    value = models.CharField(unique=True, max_length=255)  # prevent duplicate strings
    length = models.IntegerField()
    is_palindrome = models.BooleanField()
    unique_characters = models.IntegerField()
    word_count = models.IntegerField()
    character_frequency_map = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["is_palindrome"]),
            models.Index(fields=["length"]),
            models.Index(fields=["word_count"]),
            
        ]
        verbose_name = "Analyzed String"

    def clean(self):
        """Validate value before saving."""
        if not isinstance(self.value, str):
            raise ValidationError("The 'value' field must be a string.")

        if not self.value.strip():
            raise ValidationError("The 'value' field cannot be empty.")

    def save(self, *args, **kwargs):
        """Compute and populate properties automatically before saving."""
        self.clean()  # run validation

        # Compute hash (used as ID)
        if not self.id:  # only set ID on first save to avoid PK change
            self.id = compute_sha256(self.value)

        text = self.value
        text_lower = text.lower()

        # --- Compute properties ---
        self.length = len(text)
        self.is_palindrome = text_lower == text_lower[::-1]
        self.unique_characters = len(set(text_lower))
        self.word_count = len(text.split())

        # Character frequency map (case-insensitive)
        freq = {}
        for ch in text_lower:
            freq[ch] = freq.get(ch, 0) + 1
        self.character_frequency_map = freq

        # Save to DB
        super().save(*args, **kwargs)

    def __str__(self):
        """Readable representation in admin panel."""
        return f"{self.value[:30]}{'...' if len(self.value) > 30 else ''}"
