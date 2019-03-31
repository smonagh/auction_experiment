from channels.routing import route
from .consumers import ws_message, ws_connect, ws_disconnect
from otree.channels.routing import channel_routing
from channels.routing import include, route_class


housing_auction_routing = [route("websocket.connect",
                # ws_connect,  path=r'^/(?P<group_name>\w+)$'),
                # route("websocket.receive",
                # ws_message,  path=r'^/(?P<group_name>\w+)$'),
                # route("websocket.disconnect",
                # ws_disconnect,  path=r'^/(?P<group_name>\w+)$'), ]
                ws_connect,  path=r"^/chat\/(?P<group_name>[a-zA-Z0-9_/-]+)$"),
                route("websocket.receive",
                ws_message,  path=r"^/chat/(?P<group_name>[a-zA-Z0-9_/-]+)$"),
                route("websocket.disconnect",
                ws_disconnect,  path=r"^/chat/(?P<group_name>[a-zA-Z0-9_/-]+)$"),]

channel_routing += [
include(housing_auction_routing, path=r"^/housing_auction_4"),
#include(housing_auction_routing, path=r"^/telephone_market"),
]