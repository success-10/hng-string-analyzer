from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import AnalyzedString, compute_sha256


class AnalyzedStringTests(APITestCase):
    def setUp(self):
        """Create initial test data."""
        self.base_url = reverse("string-list-create")
        self.string_1 = "madam"
        self.string_2 = "hello world"
        self.hash_1 = compute_sha256(self.string_1)

        self.obj_1 = AnalyzedString.objects.create(value=self.string_1)
        self.obj_2 = AnalyzedString.objects.create(value=self.string_2)

    # ---------- Model Tests ----------
    def test_model_auto_fields(self):
        """Ensure model auto fields (length, palindrome, freq map) are computed."""
        self.assertEqual(self.obj_1.length, 5)
        self.assertTrue(self.obj_1.is_palindrome)
        self.assertEqual(self.obj_2.word_count, 2)
        self.assertIn("h", self.obj_2.character_frequency_map)
        self.assertEqual(len(self.obj_1.id), 64)

    # ---------- POST /strings ----------
    def test_create_new_string_success(self):
        """Test creating a new analyzed string."""
        data = {"value": "racecar"}
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("properties", response.data)
        self.assertTrue(response.data["properties"]["is_palindrome"])

    def test_create_duplicate_string(self):
        """Test preventing duplicate string creation."""
        data = {"value": self.string_1}
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("String already exists", response.data["detail"])

    def test_create_invalid_string_type(self):
        """Reject non-string inputs."""
        data = {"value": 12345}
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_empty_string(self):
        """Reject empty or whitespace-only strings."""
        data = {"value": "   "}
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------- GET /strings ----------
    def test_list_strings(self):
        """Fetch list of analyzed strings."""
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_list_filter_palindrome(self):
        """Filter by palindrome strings."""
        response = self.client.get(self.base_url + "?is_palindrome=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        for item in results:
            self.assertTrue(item["properties"]["is_palindrome"])

    # ---------- GET /strings/<string_value> ----------
    def test_get_string_by_value(self):
        """Retrieve analyzed string using its value."""
        url = reverse("detail_string", args=[self.string_1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], self.string_1)

    def test_get_string_by_hash(self):
        """Retrieve analyzed string using its SHA-256 hash."""
        url = reverse("detail_string", args=[self.hash_1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], self.string_1)

    def test_get_nonexistent_string(self):
        """Handle missing string gracefully."""
        url = reverse("detail_string", args=["notfound"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------- DELETE /strings/<string_value> ----------
    def test_delete_existing_string(self):
        """Delete an existing string."""
        url = reverse("detail_string", args=[self.string_2])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AnalyzedString.objects.filter(value=self.string_2).exists())

    def test_delete_nonexistent_string(self):
        """Try deleting a non-existing string."""
        url = reverse("detail_string", args=["randomtext"])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------- Natural Language Filter ----------
    def test_natural_language_query(self):
        """Test natural language query endpoint."""
        url = reverse("natlang_filter")
        response = self.client.get(url, {"query": "show palindromes"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("interpreted_query", response.data)

    def test_natural_language_query_missing_param(self):
        """Ensure query parameter is required."""
        url = reverse("natlang_filter")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("query parameter required", response.data["detail"])
