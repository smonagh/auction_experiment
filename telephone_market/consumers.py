from channels import Group
from channels.sessions import channel_session
from django.db import connection
from .models import Player as OtreePlayer
from .models import Group as OtreeGroup
from .models import Auction
from datetime import datetime
import json
import time
from ast import literal_eval

def ws_connect(message, group_name):
    """Websocket connection function"""
    print("chat connecting")
    Group(group_name).add(message.reply_channel)

def ws_message(message, group_name):
    """Websocket message function"""


    #group_id = group_name[5:]
    jsonmessage = json.loads(message.content['text'])
    myplayer = OtreePlayer.objects.get(id=jsonmessage['player_id'])
    mygroup = OtreeGroup.objects.get(id=jsonmessage['group_id'])
    if (jsonmessage['identifier'] == "msg"):
        textforgroup = json.dumps(jsonmessage)
        myplayer.bidding_log = myplayer.bidding_log + "[auction][" + str(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')) + "]: bid made: " + str(textforgroup)
        myplayer.save()
        Group(group_name).send({
            "text": textforgroup,
        })
    else:



        if (myplayer.player_type == "buyer"):
            opponent = mygroup.get_player_by_id(jsonmessage['object_id'] * 2)
        else:
            opponent = mygroup.get_player_by_id(jsonmessage['object_id'] * 2 - 1)

        #save_auction(jsonmessage, mygroup, myplayer)
        if (jsonmessage['bidvalue'] > 0):
            bids_list = literal_eval(myplayer.player_offers)
            if any(x > 0 for x in bids_list):
                # return
                # an error will be interpreted as decline
                jsonmessage['body'] = 0
                jsonmessage['bidvalue'] = 0

        bidvalue = jsonmessage['bidvalue']

        bids_list = literal_eval(myplayer.player_offers)
        bids_list[jsonmessage['object_id'] - 1] = bidvalue
        myplayer.player_offers=str(bids_list)

        bids_list = literal_eval(opponent.offers_to_player)
        bids_list[jsonmessage['my_id']] = bidvalue
        opponent.offers_to_player = str(bids_list)

        if (jsonmessage['bidvalue'] > 0):
            if (jsonmessage['body'] == " accepted"):
                jsonmessage['body'] = jsonmessage['nickname'] + " accepted " + str(jsonmessage['bidvalue'])
            else:
                jsonmessage['body'] = jsonmessage['nickname'] + " offers " + str(jsonmessage['bidvalue'])

        else:
            jsonmessage['body'] = jsonmessage['nickname'] + " declined"

            bids_list = literal_eval(opponent.player_offers)
            bids_list[jsonmessage['my_id']] = 0
            opponent.player_offers = str(bids_list)

            bids_list = literal_eval(myplayer.offers_to_player)
            bids_list[jsonmessage['object_id'] - 1] = 0
            myplayer.offers_to_player = str(bids_list)



        textforgroup = json.dumps(jsonmessage)
        myplayer.bidding_log = myplayer.bidding_log + "[auction][" + str(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')) + "]: bid made: " + str(textforgroup)
        opponent.bidding_log = opponent.bidding_log + "[auction][" + str(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')) + "]: bid made: " + str(textforgroup)

        myplayer.save()
        opponent.save()

        Group(group_name).send({
            "text": textforgroup,
        })

def ws_disconnect(message, group_name):
    """Websocket close function"""
    Group(group_name).discard(message.reply_channel)

def save_auction(message,group,player):
    """
    Function creates a new entry to save to the auction table
    """
    # if message['is_ask']==0:
    #if message['identifier'] == 'bid':
    bidvalue = message['bidvalue']
    # auction = Auction(subsession_id = group.subsession.id,group_id=group.id_in_subsession,
    #                       player_id=message['player_id'],id_in_group=player.id_in_group,
    #                       object_id=message['object_id'],player_bid=bidvalue,
    #                       last_bid=0,ask_price=0,
    #                       round_number=group.subsession.round_number,
    #                       time_stamp=str(datetime.now()))
    bids_list = literal_eval(player.bids_list)
    bids_list[message['object_id'] - 1] = bidvalue
    player.save()

    #else:
        # ask
     #   auction = Auction(subsession_id=group.subsession.id, group_id=group.id_in_subsession,
      #                    player_id=message['player_id'], id_in_group=message['id_in_group'],
       #                   object_id=message['object_id'], player_bid=message['bid'],
        #                  last_bid=message['standing_bid'], ask_price=message['ask_price'],
         #                 round_number=group.subsession.round_number,
          #                time_stamp=str(datetime.now()))
    # else:
    #     auction = Auction(subsession_id=group.subsession.id, group_id=group.id_in_subsession,
    #                       player_id=message['player_id'], id_in_group=message['id_in_group'],
    #                       object_id=message['object_id'], player_bid=message['bid'],
    #                       last_bid=message['standing_bid'], ask_price=message['bid'],
    #                       round_number=group.subsession.round_number,
    #                       time_stamp=str(datetime.now()))

    auction.save()


def update_price(message,group):
    """Update group bid entry in database"""
    if message['identifier'] == 'bid':
        # Get object id from message
        object_id = message['vars']['object_id']
        bids_list = literal_eval(group.group_bids)
        # Change value in bids list to reflect new highest bid
        bids_list[object_id - 1] = message['vars']['bid']
        # Update value in database
        group.group_bids = str(bids_list)
        return_dict = {}
        return_dict['highest_bid'] = 'False'
        return_dict['bid'] = bids_list[object_id - 1]
        return_dict['bidder_id'] = message['vars']['player_id']
        return_dict['budget'] = group.get_player_budget(message['vars']['id_in_group'])
        return_dict['object_id'] = object_id
    else:
        # Get object id from message
        object_id = message['vars']['object_id']
        asks_list = literal_eval(group.group_asks)
        # Change value in asks list to reflect new highest ask
        asks_list[object_id - 1] = message['vars']['ask_price']
        # Update value in database
        group.group_asks = str(asks_list)
        return_dict = {}
        return_dict['highest_bid'] = 'False'
        return_dict['ask_price'] = asks_list[object_id - 1]
        return_dict['bidder_id'] = message['vars']['player_id']
        return_dict['budget'] = group.get_player_budget(message['vars']['id_in_group'])
        return_dict['object_id'] = object_id
    # return_dict['is_ask'] = message['vars']['is_ask']
    return return_dict

def check_bid_above_ask(group,message):
    object_id = message['vars']['object_id']
    check = False

    # Connect to auction base and find the current max bids for objects
    cursor = connection.cursor()
    cursor.execute("""SELECT ask_price FROM
                        housing_auction_4_auction WHERE round_number = {} AND
                        group_id = {} AND subsession_id = {} AND object_id = {}
                          ;""".format(group.round_number, group.id_in_subsession,
                                      group.subsession_id,object_id))
    objects_returned = cursor.fetchall()
    if objects_returned[0][0]>0:
        check = True

    return check

def check_highest_bidder(group,message):
    """
    Check to see if the player is already the highest bidder
    """
    # Get player id and initialize check to false
    player_id = message['vars']['player_id']
    check = False

    # Connect to auction base and find the current max bids for objects
    cursor = connection.cursor()
    cursor.execute("""SELECT object_id,MAX(player_bid) FROM
                    housing_auction_4_auction WHERE round_number = {} AND
                    group_id = {} AND subsession_id = {} GROUP BY object_id
                      ;""".format(group.round_number,group.id_in_subsession,
                      group.subsession_id))
    objects_returned = cursor.fetchall()

    # Find the player id associated with each of the max bids and add to
    # result list
    result_list = []
    for i in objects_returned:
        cursor.execute('''SELECT player_id FROM housing_auction_4_auction WHERE
                        round_number = {} AND object_id = {} AND subsession_id = {}
                        AND player_bid = {} AND group_id = {};
                        '''.format(group.subsession.round_number,
                                   i[0],group.subsession.id,
                                   i[1],group.id_in_subsession))
        result = cursor.fetchall()
        result_list.append(result)
    # If player id matches any that are in the list prevent process from finishing
    for i in result_list:
        if i[0][0] == player_id:
            check = True

    return check

def return_auction_info(object_id,round_number,subsession_id,group_id):

    cursor = connection.cursor()
    # SELECT all bids for the selected object
    cursor.execute("""SELECT player_id,id_in_group,object_id,player_bid,
                      ask_price FROM housing_auction_4_auction WHERE
                      round_number = {} AND object_id = {} AND
                      subsession_id = {} AND group_id = {}
                      """.format(round_number,object_id,subsession_id,group_id))
    items_returned = cursor.fetchall()
    # Find the highest bid for the selected object
    cur_max = items_returned[0]
    cur_max_bid = items_returned[0][3]
    for i in items_returned:
        if i[3]> cur_max_bid:
            cur_max = i
            cur_max_bid = i[3]

    # Define vars for return
    player_id = cur_max[0]
    id_in_group = cur_max[1]
    highest_bid = cur_max[3]
    ask_price = cur_max[4]
    cursor.close()
    return player_id,id_in_group, highest_bid, ask_price
