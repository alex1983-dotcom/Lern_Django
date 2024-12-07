from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def index(request):
    html_content = "<html><body><h1>Hello, world. You're at the polls index.</h1></body></html>"
    return HttpResponse(html_content, content_type='text/html')
