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
        highest_bidder = check_budget_constraint(mygroup,jsonmessage)
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
        # If not, send message to update information on players screen
        else:
            save_auction(jsonmessage,mygroup,0)
            my_dict = update_price(jsonmessage,mygroup)
            print(my_dict)
            mygroup.save()
            for player in mygroup.get_players():
                print(player)
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
    auction = Auction(subsession_id = group.subsession.id,group_id=group.id_in_subsession,
                      player_id=message['player_id'],id_in_group=message['id_in_group'],
                      object_id=message['object_id'],player_bid=message['bid'],
                      last_bid=message['standing_bid'],ask_price=message['ask_price'],
                      round_number=group.subsession.round_number,
                      time_stamp=str(datetime.now()))
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
    return_dict['id'] = message['vars']['object_id']
    return_dict['budget'] = group.get_player_budget(message['vars']['player_id'])
    return return_dict

def check_budget_constraint(group,message):
    """
    Check to see if the player is currently the bidding more than their
    endowment
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
        cursor.execute('''SELECT player_id, player_bid FROM housing_auction_4_auction WHERE
                        round_number = {} AND object_id = {} AND subsession_id = {}
                        AND player_bid = {} AND group_id = {};
                        '''.format(group.subsession.round_number,
                                   i[0],group.subsession.id,
                                   i[1],group.id_in_subsession))
        result = cursor.fetchall()
        result_list.append(result)
    # If player id matches any that are in the result list return amount bidded
    amount_spent = 0
    for i in result_list:
        if i[0][0] == player_id and i[0][1] > 0:
            amount_spent += i[0][1]
    # If player's outstanding bids are more than endowment return check = True
    if amount_spent > group.get_player_endowment(message['vars']['player_id']):
        check = True
    else:
        # update player budget information in Database
        print('***amount spent:  ', 0 - amount_spent - int(message['vars']['bid']))
        print(group.get_player_by_id(message['vars']['player_id']).budget)
        player = group.get_player_by_id(message['vars']['player_id'])
        player.budget = player.endowment - amount_spent - int(message['vars']['bid'])
        print(player,player.budget)
        player.save()
        print(group.get_player_by_id(message['vars']['player_id']).budget)
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
    Function updates group_fin_bid to indicate a player has
    finished bidding.
    """
    # Get player id
    player_id = jsonmessage['vars']['player_id']
    # Convert backend data from string to list
    group_fin_bid = literal_eval(mygroup.group_fin_bid)
    # Find relevant buyer id
    buyer_id = mygroup.get_player_buyer_id(player_id)
    # Change relevant entry in group fin bids
    group_fin_bid[buyer_id] = True
    # Convert back to string and write to Database
    mygroup.group_fin_bid = str(group_fin_bid)
    mygroup.save()
    # Check to see if all players have clicked the button
    check = True
    for i in group_fin_bid:
        if i == False:
            check = False
    if check:
        return 'done'
    else:
        return 'not done'
