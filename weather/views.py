import requests
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import City
from .forms import CityForm

OPENWEATHER_APPID = os.environ.get("OPENWEATHER_APPID", "")
OPENWEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
    "?q={}&units=metric&appid=" + OPENWEATHER_APPID
)



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
            city_name = form.cleaned_data['name']
            if not City.objects.filter(name=city_name).exists():
                form.save()
            return redirect('home')

    form = CityForm()
    all_cities = []

    for city in City.objects.all():
        res = requests.get(OPENWEATHER_URL.format(city.name)).json()
        if res.get("cod") == 200:
            all_cities.append({
                "id": city.id,
                "city": city.name,
                "temp": res["main"]["temp"],
                "icon": res["weather"][0]["icon"],
            })

    context = {"all_info": all_cities, "form": form}
    return render(request, 'weather/index.html', context)


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
        messages.error(request, "Неправильний логін або пароль!")

    return render(request, 'weather/login.html')


@require_POST
def logout_user(request):
    logout(request)
    return redirect('home')
