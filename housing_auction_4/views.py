from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Auction
from datetime import datetime
from ast import literal_eval
from math import ceil

class Instructions_Seller(Page):
    """
    Page that displays instructions to sellers
    """
    # Only display in the first round
    def is_displayed(self):
        if self.subsession.round_number == 1 and self.player.player_type == 'seller':
            return self

    # Adjust what instructions are being display according to treatments being
    # run.
    def vars_for_template(self):
        return {'treatment_string':self.session.config['treatment_string'],
                'player_type':self.player.player_type,'timeout_duration':self.session.config['timeout_duration']}

    form_model = models.Player
    form_fields = ['ask_price']

class Instructions_Buyer(Page):
    """
    Page that displays instructions to buyers
    """
    # Only display in the first round
    def is_displayed(self):
        if self.subsession.round_number == 1 and self.player.player_type == 'buyer':
            return self

    # Adjust what instructions are being display according to treatments being
    # run.
    def vars_for_template(self):
        return {'treatment_string':self.subsession.treatment,
                'player_type':self.player.player_type,'timeout_duration':self.session.config['timeout_duration']}

class PreWaitPage(WaitPage):

    def after_all_players_arrive(self):
        pass

class SetAsk(Page):
    """
    Page where sellers can set there ask prices.
    """

    def is_displayed(self):
        if self.player.player_type == 'seller' and self.subsession.treatment == 'minimum_price':
            return self

    def vars_for_template(self):
        # Return seller reservation value for assigned object
        return {'reservation_value':self.player.get_seller_reservation(),
                'assigned_object':self.player.assigned_object}

    form_model = models.Player
    form_fields = ['ask_price']

class Bid(Page):
    """
    Page where buyers can submit their bids for objects.
    """

    def vars_for_template(self):
        # Create record in database for start time
        auction = Auction(time_stamp=str(datetime.now()),
                          group_id=self.group.id_in_subsession,
                          subsession_id=self.subsession.id,
                          round_number=self.subsession.round_number,
                          player_id = -1,
                          id_in_group = -1,
                          object_id = -1,
                          player_bid = -1,
                          last_bid = -1,
                          ask_price = -1)
        auction.save()
        # Return a list of ask prices, reservation values,and bid = 0 for
        # each object that is in play.
        object_list = ['Widget {}'.format(i) for i in range(1,
                                                    Constants.group_split + 1)]
        # Convert data from strings into lists
        bid_list = literal_eval(self.group.group_bids)
        ask_list = literal_eval(self.group.group_asks)
        res_list = literal_eval(self.player.player_reservations)
        seller_name = ['Seller {}'.format(i) for i in range(1,
                                                    Constants.group_split + 1)]
        # Create a zip of all four lists
        auction_zip = zip(seller_name,object_list,ask_list,res_list,bid_list)
        return {'player_type':self.player.player_type,
                'auction_zip':auction_zip,
                'object_list':object_list,
                'time_left':self.group.time_elapsed,
                'treatment':self.subsession.treatment,
                'end_on_timer':Constants.end_on_timer,
                'timeout_duration': self.session.config['timeout_duration']}


class Bid_Buyer_MP(Bid):
    """Page for buyers in the full information treatment"""
    def is_displayed(self):
        if self.player.player_type == 'buyer' and \
         self.subsession.treatment == 'minimum_price':
            return self

class Bid_Seller_MP(Bid):
    """Page for seller in the full information treatment"""
    def is_displayed(self):
        if self.player.player_type == 'seller' and \
         self.subsession.treatment == 'minimum_price':
            return self

class Bid_Buyer_SB(Bid):
    """Page for buyers in the no information treatment"""
    def is_displayed(self):
        if self.player.player_type == 'buyer' and \
         self.subsession.treatment == 'sellers_bid':
            return self

class Bid_Seller_SB(Bid):
    """Page for buyers in the no information treatment"""
    def is_displayed(self):
        if self.player.player_type == 'seller' and \
         self.subsession.treatment == 'sellers_bid':
            return self

class Bid_Buyer_DA(Bid):
    """Page for buyers in the no information treatment"""

    def is_displayed(self):
        if self.player.player_type == 'buyer' and \
                self.subsession.treatment == 'double_auction':
            return self

class Bid_Seller_DA(Bid):
    """Page for buyers in the no information treatment"""

    def is_displayed(self):
        if self.player.player_type == 'seller' and \
                self.subsession.treatment == 'double_auction':
            return self

class BidWaitPage(WaitPage):

    def after_all_players_arrive(self):
        """Set group ask variable to be used in next template"""
        # Check to make sure that asks are above seller reservations
        for player in self.group.get_players():
            if player.player_type == "seller":
                if self.subsession.treatment == 'minimum_price':
                    if player.ask_price < player.get_seller_reservation():
                        player.ask_price = player.get_seller_reservation()
                else:
                    #player.ask_price = 0
                    player.ask_price = 0
        group_asks = self.group.get_group_asks()
        self.group.group_asks = str(group_asks)

class ResultsWaitPage(WaitPage):
    """Wait page afte the auction stage"""
    def after_all_players_arrive(self):
        # Create record in database for endtime
        auction = Auction(time_stamp=str(datetime.now()),
                          group_id=self.group.id_in_subsession,
                          subsession_id=self.subsession.id,
                          round_number=self.subsession.round_number,
                          player_id = -1,
                          id_in_group = -1,
                          object_id = -1,
                          player_bid = -1,
                          last_bid = -1,
                          ask_price = -1)
        auction.save()
        self.group.record_winners(self.subsession.round_number,
        self.subsession.id,self.group.id_in_subsession)


class Results(Page):
    """Results shown after each period"""
    def vars_for_template(self):
        object_list = ['Widget {}'.format(i) for i in range(1,
                                                    Constants.group_split + 1)]
        ask_list = literal_eval(self.group.group_asks)
        bid_list = literal_eval(self.group.group_bids)
        was_traded = literal_eval(self.group.was_traded)
        was_traded_to_seller = literal_eval(self.group.was_traded_to_seller)
        res_list = literal_eval(self.player.player_reservations)
        result_zip = zip(object_list,ask_list,bid_list,res_list,was_traded,was_traded_to_seller)
        return{'player_type':self.player.player_type,'result_zip':result_zip}

    def before_next_page(self):
        # if last round calculate final payoffs
        if self.subsession.round_number == Constants.num_rounds:
            self.player.set_final_payoff()

class FinalResults(Page):
    """Disply final earnings in the game"""
    def is_displayed(self):
        # If the last round of the game then return page
        if self.subsession.round_number == Constants.num_rounds:
            return self
    def vars_for_template(self):
        payout_list = []
        for i in self.player.in_all_rounds():
            payout_list.append(i.payout)
        return {'player_payouts':payout_list,
                'rounded_payout':ceil(self.player.final_us_payout*4)/4+5}


page_sequence = [
    Instructions_Seller,
    Instructions_Buyer,
    PreWaitPage,
    SetAsk,
    BidWaitPage,
    Bid_Buyer_MP,
    Bid_Seller_MP,
    Bid_Buyer_SB,
    Bid_Seller_SB,
    Bid_Buyer_DA,
    Bid_Seller_DA,
    ResultsWaitPage,
    Results,
    FinalResults
]
