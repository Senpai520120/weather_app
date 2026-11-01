import logging

import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import City
from .forms import CityForm

logger = logging.getLogger(__name__)

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 5  # seconds


class WeatherError(Exception):
    """Weather data could not be fetched; the message is safe to show to users."""


class CityNotFound(WeatherError):
    pass


def get_weather(city_name):
    """Return {"temp": ..., "icon": ...} for a city or raise WeatherError."""
    if not settings.OPENWEATHER_APPID:
        raise WeatherError("OpenWeatherMap API key is not configured (set OPENWEATHER_APPID).")

    try:
        response = requests.get(
            OPENWEATHER_URL,
            params={"q": city_name, "units": "metric", "appid": settings.OPENWEATHER_APPID},
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        logger.exception("OpenWeatherMap request failed for %r", city_name)
        raise WeatherError("Weather service is unavailable. Please try again later.")

    if response.status_code == 401:
        raise WeatherError("OpenWeatherMap API key is invalid.")
    if response.status_code == 404:
        raise CityNotFound(f"City \"{city_name}\" was not found.")
    if response.status_code != 200:
        raise WeatherError("Weather service returned an error. Please try again later.")

    try:
        return {"temp": data["main"]["temp"], "icon": data["weather"][0]["icon"]}
    except (KeyError, IndexError, TypeError):
        raise WeatherError("Weather service returned unexpected data.")


def register_user(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'weather/register.html', {'form': form})


def index(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('login')

        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name'].strip()
            if City.objects.filter(name__iexact=city_name).exists():
                messages.info(request, f'"{city_name}" is already in the list.')
                return redirect('home')
            try:
                get_weather(city_name)
            except CityNotFound as exc:
                messages.error(request, str(exc))
                return redirect('home')
            except WeatherError:
                # Keep the city; the error is shown next to it on the list.
                pass
            City.objects.create(name=city_name)
            return redirect('home')

    form = CityForm()
    all_cities = []
    errors = set()

    for city in City.objects.all():
        info = {"id": city.id, "city": city.name}
        try:
            info.update(get_weather(city.name))
        except WeatherError as exc:
            info["error"] = str(exc)
            errors.add(str(exc))
        all_cities.append(info)

    context = {"all_info": all_cities, "form": form, "errors": sorted(errors)}
    return render(request, 'weather/index.html', context)


@require_POST
@login_required(login_url='login')
def delete_city(request, city_id):
    city = get_object_or_404(City, id=city_id)
    city.delete()
    return redirect('home')


def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, "Invalid username or password.")

    return render(request, 'weather/login.html')


@require_POST
def logout_user(request):
    logout(request)
    return redirect('home')
