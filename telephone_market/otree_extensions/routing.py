#from channels.routing import route
import channels
from telephone_market import consumers
# chat/routing.py
from django.urls import re_path

websocket_routes = [
    re_path(r'telephone_market/chat/(?P<room_name>[a-zA-Z0-9_/-]+)/$', consumers.ChatConsumer),
]
