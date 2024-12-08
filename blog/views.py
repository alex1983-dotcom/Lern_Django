from django.shortcuts import render

# Create your views here.
# blog/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world. You're at the blog index.")
