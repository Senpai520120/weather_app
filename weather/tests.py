from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import City


def api_response(status_code, payload):
    response = Mock(status_code=status_code)
    response.json.return_value = payload
    return response


LONDON_OK = api_response(200, {"main": {"temp": 12.5}, "weather": [{"icon": "04d"}]})
NOT_FOUND = api_response(404, {"cod": "404", "message": "city not found"})
BAD_KEY = api_response(401, {"cod": 401, "message": "Invalid API key"})


@override_settings(OPENWEATHER_APPID="test-key")
class IndexViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="s3cret-pass!")

    @patch("weather.views.requests.get", return_value=LONDON_OK)
    def test_shows_weather_for_saved_cities(self, mock_get):
        City.objects.create(name="London")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "London")
        self.assertContains(response, "12.5")
        self.assertEqual(mock_get.call_args.kwargs["params"]["q"], "London")
        self.assertIn("timeout", mock_get.call_args.kwargs)

    @patch("weather.views.requests.get", side_effect=requests.ConnectionError)
    def test_network_error_does_not_crash(self, mock_get):
        City.objects.create(name="London")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weather service is unavailable")

    @patch("weather.views.requests.get", return_value=BAD_KEY)
    def test_invalid_api_key_shows_message(self, mock_get):
        City.objects.create(name="London")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API key is invalid")

    @override_settings(OPENWEATHER_APPID="")
    @patch("weather.views.requests.get")
    def test_missing_api_key_shows_message_without_calling_api(self, mock_get):
        City.objects.create(name="London")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API key is not configured")
        mock_get.assert_not_called()


@override_settings(OPENWEATHER_APPID="test-key")
class CityManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="s3cret-pass!")

    @patch("weather.views.requests.get", return_value=LONDON_OK)
    def test_anonymous_user_cannot_add_city(self, mock_get):
        response = self.client.post(reverse("home"), {"name": "London"})
        self.assertRedirects(response, reverse("login"))
        self.assertFalse(City.objects.exists())

    @patch("weather.views.requests.get", return_value=LONDON_OK)
    def test_signed_in_user_can_add_city(self, mock_get):
        self.client.force_login(self.user)
        response = self.client.post(reverse("home"), {"name": "London"})
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(City.objects.filter(name="London").exists())

    @patch("weather.views.requests.get", return_value=LONDON_OK)
    def test_duplicate_city_is_not_added(self, mock_get):
        City.objects.create(name="London")
        self.client.force_login(self.user)
        self.client.post(reverse("home"), {"name": "london"})
        self.assertEqual(City.objects.count(), 1)

    @patch("weather.views.requests.get", return_value=NOT_FOUND)
    def test_unknown_city_is_rejected(self, mock_get):
        self.client.force_login(self.user)
        response = self.client.post(reverse("home"), {"name": "Atlantis"}, follow=True)
        self.assertFalse(City.objects.exists())
        self.assertContains(response, "was not found")

    def test_delete_requires_post_and_login(self):
        city = City.objects.create(name="London")
        url = reverse("delete_city", args=[city.id])

        self.assertEqual(self.client.post(url).status_code, 302)  # redirected to login
        self.assertTrue(City.objects.filter(id=city.id).exists())

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertFalse(City.objects.filter(id=city.id).exists())


class AuthTests(TestCase):
    def test_register_logs_user_in(self):
        response = self.client.post(reverse("register"), {
            "username": "bob",
            "password1": "Very-long-pass-123",
            "password2": "Very-long-pass-123",
        })
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username="bob").exists())

    def test_login_with_wrong_password_shows_error(self):
        User.objects.create_user("alice", password="s3cret-pass!")
        response = self.client.post(reverse("login"), {"username": "alice", "password": "nope"})
        self.assertContains(response, "Invalid username or password")
