from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from otree.db.models import Model, ForeignKey
import numpy as np
from ast import literal_eval
import itertools
import random
from math import ceil

author = 'Steven Monaghan'

doc = """
Housing Auction
"""

class Constants(BaseConstants):
    """
    treatment_list contains that possible treatments that will be run in the
    session. Current options include minimum_price and sellers_bid.
    end_on_timer if true will end trading stage after 30 seconds of inactivity.
    """
    name_in_url = 'housing_auction_4'
    seller_res_min = 1
    seller_res_max = 10
    buyer_res_min = 1
    buyer_res_max = 10
    end_on_timer = 1
    players_per_group = 6
    periods_per_treatment = 5 ###
    num_rounds = periods_per_treatment
    conversion_rate = 5
    group_split = int(players_per_group / 2)


class Auction(Model):
    # Database to record real time auction activity
    subsession_id = models.IntegerField()
    group_id = models.IntegerField()
    player_id = models.IntegerField()
    id_in_group = models.IntegerField()
    object_id = models.IntegerField()
    player_bid = models.IntegerField()
    last_bid = models.IntegerField()
    last_price = models.IntegerField()
    ask_price = models.IntegerField()
    round_number = models.IntegerField()
    time_stamp = models.CharField()
    treatment = models.CharField()

class Subsession(BaseSubsession):
    treatment = models.CharField()
    def before_session_starts(self):
        """Initialize values at the start of the session"""
        if self.round_number == 1:
            self.initial_assignment()
        else:
            self.subsequent_assignment()

    def initial_assignment(self):
        """Define assignment that takes place on the first round of Game"""
        # Assign subession the first treatment in treatment list
        self.treatment = self.session.config['treatment_string']
        # Set up iterator for player types
        iterator = itertools.cycle(['buyer', 'seller'])

        # Generate a list of integers to index seller objects and randomize
        object_id_list = [i for i in range(1, Constants.group_split + 1)]
        random.shuffle(object_id_list)

        # Set values for each group of players
        for group in self.get_groups():
            # Define group level variables
            group_bids = [0 for i in range(0,Constants.group_split)]
            group_asks = [0 for i in range(0,Constants.group_split)]
            was_traded = [False for i in range(0,Constants.group_split)]
            was_traded_to_seller = [False for i in range(0, Constants.group_split)]
            # Convert to strings for database
            group.group_bids = str(group_bids)
            group.group_asks = str(group_asks)
            group.was_traded = str(was_traded)
            group.was_traded_to_seller = str(was_traded_to_seller)
            group.bidding_log = 'First round started \n'

            # Define player level variables
            # Create index for seller object assignment
            seller_index = 0
            buyer_index = 0
            for player in group.get_players():
                # Assign player type
                player.player_type = next(iterator)
                player.budget = player.endowment
                # Assign player reservation values
                my_dict = self.reservation_assignment(player,
                player.player_type)
                player.player_reservations = str(my_dict)
                # Assign intial variable for "finished bidding"
                player.fin_bid = False
                # If player is a seller assign him an object and give id
                if player.player_type == 'seller':
                    #This is for random assignment of seller objects
                    #player.assigned_object = object_id_list[seller_index]
                    if player.id_in_group == 2:
                        player.assigned_object = 1
                    elif player.id_in_group == 4:
                        player.assigned_object = 2
                    elif player.id_in_group == 6:
                        player.assigned_object = 3
                    player.seller_id = seller_index
                    seller_index += 1
                # If player is a buyer given him a buyer id
                if player.player_type == 'buyer':
                    player.buyer_id = buyer_index
                    buyer_index += 1


    def subsequent_assignment(self):
        """Define assignment that takes place in game rounds after first"""

        # Assign players the same reservation values that they were assigned
        # in round 1
        for group in self.get_groups():
            group.group_bids = group.in_round(1).group_bids
            group.group_asks = group.in_round(1).group_asks
            group.was_traded = group.in_round(1).was_traded
            group.was_traded_to_seller = group.in_round(1).was_traded_to_seller
            group.bidding_log = 'Round ' + str(self.round_number) + ' started.\n'

            # Define player level variables
            for player in group.get_players():
                player.budget = player.endowment
                player.player_reservations = player.in_round(1).player_reservations
                player.assigned_object = player.in_round(1).assigned_object
                player.player_type = player.in_round(1).player_type
                player.buyer_id = player.in_round(1).buyer_id
                player.seller_id = player.in_round(1).seller_id
                player.fin_bid = False;


        # Assign subsession treatment value
        if self.round_number <= Constants.periods_per_treatment:
            self.treatment = self.session.config['treatment_string']
        # elif self.round_number > Constants.periods_per_treatment:
        #     self.treatment = self.session. treatment_list[1]
        # elif self.round_number > Constants.periods_per_treatment * 2:
        #     self.treatment = self.session.treatment_list[2]

    def reservation_assignment(self,player,player_type):
        """Assign reservation values to player according to player type
           and return a list"""
        # Create a dictionary entry for each reseravtion values
        reservation_list = []
        """
        for i in range(0,Constants.group_split):
            if player_type == 'buyer':
                reservation_list.append(int(
                                  np.random.uniform(Constants.buyer_res_min,
                                  Constants.buyer_res_max,1)[0]))
            elif player_type == 'seller':
                reservation_list.append(
                int(np.random.uniform(Constants.seller_res_min,
                                  Constants.seller_res_max,1)[0]))
        """
        if player.id_in_group == 1:
            reservation_list.append(23*20)
            reservation_list.append(22*20)
            reservation_list.append(21*20)
        elif player.id_in_group == 3:
            reservation_list.append(26*20)
            reservation_list.append(24*20)
            reservation_list.append(22*20)
        elif player.id_in_group == 5:
            reservation_list.append(20*20)
            reservation_list.append(21*20)
            reservation_list.append(17*20)
        elif player.id_in_group == 2:
            reservation_list.append(18*20)
            reservation_list.append(0)
            reservation_list.append(0)
        elif player.id_in_group == 4:
            reservation_list.append(0)
            reservation_list.append(15*20)
            reservation_list.append(0)
        elif player.id_in_group == 6:
            reservation_list.append(0)
            reservation_list.append(0)
            reservation_list.append(19*20)

        return reservation_list


class Group(BaseGroup):
    """
    Group class to record unique data associated with the group
    """
    auction_time = models.IntegerField(initial=0)
    group_bids = models.CharField()
    group_asks = models.CharField()
    was_traded = models.CharField()
    was_traded_to_seller = models.CharField()
    time_elapsed = models.IntegerField(initial=0)
    bidding_log = models.LongStringField()

    def get_group_asks(self):
        """Function returns a list of group ask prices"""

        ask_list = []
        # Get sellers by object id and create an ask price entry for them
        for i in range(1,Constants.group_split + 1):
            seller = self.get_seller_by_object(i)
            ask_list.append(seller.ask_price)

        return ask_list

    def get_seller_by_object(self,object_id):
        """Function to return seller by their assigned object"""
        # Loop through all players and check to see if assigned object matches
        # input
        for seller in self.get_players():
            if seller.assigned_object == object_id:
                return seller

    def get_player_buyer_id(self,player_id):
        """Get players buyer id"""
        for player in self.get_players():
            if player.id_in_subsession == player_id:
                return player.buyer_id

    def get_player_budget(self,player_id):
        """Get player remaining endowment"""
        my_player = self.get_player_by_id(player_id)
        player_budget = my_player.budget
        return player_budget

    def get_player_endowment(self,player_id):
        """Get player endowment"""
        my_player = self.get_player_by_id(player_id)
        player_endowment = my_player.endowment
        return player_endowment

    def record_winners(self,round_number,subsession_id,group_id):
        """Function to record the outcome of the auction period"""
        from . import consumers
        # Convert strings to lists
        group_bids = literal_eval(self.group_bids)
        was_traded = literal_eval(self.was_traded)
        was_traded_to_seller = literal_eval(self.was_traded_to_seller)

        for i in range(1,Constants.group_split+1):
            try:
                player_id,id_in_group,highest_bid,ask_price = \
                consumers.return_auction_info(i,round_number,
                subsession_id,group_id)
                # Set the bid for period to highest bid
                group_bids[i-1] = highest_bid
                # Check to see if object was traded
                if highest_bid >= ask_price:
                    # If query does not fail, then mark was traded true
                    was_traded[i-1] = True
                    # Set player as 'winner'
                    self.get_player_by_id(id_in_group).is_winner = True

                    if self.get_player_by_id(id_in_group).player_type == 'seller':
                        # sold to himself
                        was_traded_to_seller[i-1] = True
                        self.get_player_by_id(id_in_group).traded_with_himself = True
                        self.get_player_by_id(id_in_group).payout = 0
                        self.get_player_by_id(id_in_group).object_traded = i
                        self.get_player_by_id(id_in_group).winning_bid = highest_bid
                    else:
                        # Update player payoff
                        self.get_player_by_id(id_in_group).set_payoff(highest_bid,
                                                                      ask_price,i)
                        # Check for the corresponding seller
                        for player in self.get_players():
                            if player.assigned_object == i:
                                player.is_winner = True
                                player.set_payoff(highest_bid,ask_price,i)

            except:
                pass

            # Write was traded and group bids to database as string
            self.was_traded = str(was_traded)
            self.was_traded_to_seller = str(was_traded_to_seller)
            self.group_bids = str(group_bids)


class Player(BasePlayer):
    """
    Player class to record unique data associated with each player
    """
    ask_price = models.IntegerField(initial=Constants.seller_res_min,
    min= 1,max = 800, widget=widgets.SliderInput)
    is_winner = models.BooleanField(initial=False)
    traded_with_himself = models.BooleanField(initial=False)
    assigned_object = models.IntegerField(initial=-1)
    payout = models.IntegerField(initial=0)
    object_traded = models.IntegerField()
    object_reservation = models.IntegerField()
    winning_bid = models.IntegerField()
    final_payout = models.IntegerField()
    final_us_payout = models.FloatField()
    player_bids = models.CharField()
    player_reservations = models.CharField()
    player_type = models.CharField()
    buyer_id = models.IntegerField(initial=-1)
    seller_id = models.IntegerField(initial=-1)
    payout_round = models.IntegerField()
    endowment = models.IntegerField(initial=10)
    budget = models.IntegerField()
    fin_bid = models.BooleanField(initial=False)


    def get_seller_reservation(self):
        """ Return the seller reservation value for their assigned object"""
        # Acquire player reservation dict and convert from string
        reservation_list = literal_eval(self.player_reservations)
        # Return reservation value for assigned object
        return reservation_list[self.assigned_object - 1]

    def get_buyer_reservation(self,object_id):
        """Function to get buyers reservation value for relevant object"""
        reservation_list = literal_eval(self.player_reservations)
        reservation_for_obj = reservation_list[object_id - 1]
        return reservation_for_obj

    def set_payoff(self,bid,ask,object_id):

        if self.player_type == 'buyer':
            self.payout = self.get_buyer_reservation(object_id) - bid
            self.object_traded = object_id
            self.object_reservation = self.get_buyer_reservation(object_id)
            self.winning_bid = bid

        elif self.player_type == 'seller':
            self.payout = bid - self.get_seller_reservation()
            self.object_traded = object_id
            self.object_reservation = self.get_seller_reservation()
            self.winning_bid = bid

    def set_final_payoff(self):

        #Set round that player recieves payoff in randomly
        self.payout_round = random.randint(1,Constants.num_rounds)
        self.final_payout = self.in_round(self.payout_round).payout
        self.final_us_payout = self.final_payout/Constants.conversion_rate
        self.payoff = (ceil(self.final_us_payout*4)/4)*100
