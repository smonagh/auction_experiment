from channels import Group
from channels.sessions import channel_session
from django.db import connection
from .models import Player, Group as OtreeGroup, Constants
from .models import Auction
from datetime import datetime
import json
import time
from ast import literal_eval

def ws_connect(message, group_name):
    """Websocket connection function"""
    Group(group_name).add(message.reply_channel)

def ws_message(message, group_name):
    """Websocket message function"""
    group_id = group_name[5:]
    jsonmessage = json.loads(message.content['text'])
    mygroup = OtreeGroup.objects.get(id=group_id)
    # Check to see if soft close
    if jsonmessage['identifier'] == 'close':
        bid_status = soft_close(mygroup,jsonmessage)
        my_dict = {'bid_status':bid_status}
        textforgroup = json.dumps(my_dict)
        Group(group_name).send({
            "text": textforgroup,
        })
    elif jsonmessage['identifier'] == 'bid':
        # Check to make sure bid is within the budget constraint
        highest_bidder = check_highest_bidder(mygroup,jsonmessage)
        # If he is highest bidder send message to throw alert window
        if highest_bidder:
            my_dict = {'highest_bid':True,
            'bidder_id':jsonmessage['vars']['player_id'],
            'bid_status':'not done',
            }
            textforgroup = json.dumps(my_dict)
            Group(group_name).send({
                "text": textforgroup,
            })
        else:  # If not, send message to update information on players screen
            if Constants.end_on_timer:
                for i in mygroup.get_players():
                    i.fin_bid = False
                    i.save()
            # Send messages to players
            save_auction(jsonmessage,mygroup,0)
            my_dict = update_price(jsonmessage,mygroup)
            print("[auction]["+str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))+"]: bid made: "+ str(my_dict))
            mygroup.save()
            for player in mygroup.get_players():
                #print(player)
                player.save()
            textforgroup = json.dumps(my_dict)
            Group(group_name).send({
                    "text": textforgroup,
                    })
    elif jsonmessage['identifier'] == 'ask':
        # Check to make sure bid is within the budget constraint
        if Constants.end_on_timer:
            for i in mygroup.get_players():
                i.fin_bid = False
                i.save()
        # Send messages to players
        save_auction(jsonmessage,mygroup,0)
        my_dict = update_price(jsonmessage,mygroup)
        print("[auction]["+str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))+"]: ask made: "+ str(my_dict))
        mygroup.save()
        for player in mygroup.get_players():
            #print(player)
            player.save()
        textforgroup = json.dumps(my_dict)
        Group(group_name).send({
                "text": textforgroup,
                })

def ws_disconnect(message, group_name):
    """Websocket close function"""
    Group(group_name).discard(message.reply_channel)

def save_auction(message,group,time_left):
    """
    Function creates a new entry to save to the auction table
    """
    message = message['vars']
    # if message['is_ask']==0:
    #if message['identifier'] == 'bid':
    auction = Auction(subsession_id = group.subsession.id,group_id=group.id_in_subsession,
                          player_id=message['player_id'],id_in_group=message['id_in_group'],
                          object_id=message['object_id'],player_bid=message['bid'],
                          last_bid=message['standing_bid'],ask_price=message['ask_price'],
                          round_number=group.subsession.round_number,
                          time_stamp=str(datetime.now()))
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
    # return_dict['is_ask'] = message['vars']['is_ask']
    return return_dict

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

def soft_close(mygroup,jsonmessage):
    """
    Function updates fin_bid to indicate a player has
    finished bidding.
    """
    # Get player id
    player_id = jsonmessage['vars']['player_id']
    id_in_group = jsonmessage['vars']['id_in_group']
    # Convert backend data from string to list
    player=mygroup.get_player_by_id(id_in_group)
    player.fin_bid=True
    player.save()

    # Check to see if all players have clicked the button
    check = True
    for i in mygroup.get_players():
        if i.buyer_id > -1:
            if i.fin_bid == False:
                check = False
    if check:
        print("[auction]["+str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))+"]:round ends for group of player " + str(jsonmessage['vars']['player_id']))
        return 'done'
    else:
        return 'not done'
