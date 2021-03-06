import os
from os import environ

import dj_database_url

import otree.settings

#CHANNEL_ROUTING = 'housing_auction_4.routing.channel_routing'
#CHANNEL_ROUTING = 'telephone_market.routing.channel_routing'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_APPS = ['telephone_market']

# the environment variable OTREE_PRODUCTION controls whether Django runs in
# DEBUG mode. If OTREE_PRODUCTION==1, then DEBUG=False
if environ.get('OTREE_PRODUCTION') not in {None, '', '0'}:
    DEBUG = False
else:
    DEBUG = True

DEBUG = True

ADMIN_USERNAME = 'ICES'

# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

# don't share this with anybody.
SECRET_KEY = 'st-ueln282mhvg9k108jo45$=v!6!sf@8(c^!$%m-pj6a0!0=7'



# AUTH_LEVEL:
# If you are launching a study and want visitors to only be able to
# play your app if you provided them with a start link, set the
# environment variable OTREE_AUTH_LEVEL to STUDY.
# If you would like to put your site online in public demo mode where
# anybody can play a demo version of your game, set OTREE_AUTH_LEVEL
# to DEMO. This will allow people to play in demo mode, but not access
# the full admin interface.

AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')

# setting for integration with AWS Mturk
AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')


# e.g. EUR, CAD, GBP, CHF, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True


# e.g. en, de, fr, it, ja, zh-hans
# see: https://docs.djangoproject.com/en/1.9/topics/i18n/#term-language-code
LANGUAGE_CODE = 'en'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']

# SENTRY_DSN = ''

DEMO_PAGE_INTRO_HTML = """
Auction Experiment
"""

mturk_hit_settings = {
    'keywords': ['easy', 'bonus', 'choice', 'study'],
    'title': 'Title for your experiment',
    'description': 'Description for your experiment',
    'frame_height': 500,
    'preview_template': 'global/MTurkPreview.html',
    'minutes_allotted_per_assignment': 60,
    'expiration_hours': 7*24,  # 7 days
    # 'grant_qualification_id': 'YOUR_QUALIFICATION_ID_HERE',# to prevent retakes
    # to use qualification requirements, you need to uncomment the 'qualification' import
    # at the top of this file.
    'qualification_requirements': [],
}

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 0.01,
    'participation_fee': 5.00,
    'doc': "",
    'mturk_hit_settings': mturk_hit_settings,
}


SESSION_CONFIGS = [
        #Pit telephone market
        {'name': 'telephone_market',
         'display_name': 'Pit telephone market',
         'num_demo_participants': 6,
         # 'treatment_string':"['minimum_price','sellers_bid']",
         'treatment_string': "telephone_pit",
         'doc': """Telephone pit trading market""",
         'timeout_duration': 60*4, #60*4
         'complete_info': True,
         'app_sequence': ['telephone_market']},

        #MP
        {'name':'housing_auction_MP',
        'display_name': 'Housing Auction MP',
        'num_demo_participants': 6,
        # 'treatment_string':"['minimum_price','sellers_bid']",
        'treatment_string': "minimum_price",
        'doc':"""Enter treatments to be played in session. Must be entered in
                 the form of a list []. Options are minimum_price, sellers_bid, double_auction. 
                 Treatments are played in order entered.""",
         'timeout_duration': 50,
         'complete_info': True,
        'app_sequence': ['housing_auction_4']},

        # SB
        {'name':'housing_auction_SB',
        'display_name': 'Housing Auction SB',
        'num_demo_participants': 6,
        # 'treatment_string':"['minimum_price','sellers_bid']",
        'treatment_string': "sellers_bid",
        'doc':"""Enter treatments to be played in session. Must be entered in
                 the form of a list []. Options are minimum_price, sellers_bid, double_auction. 
                 Treatments are played in order entered.""",
        'timeout_duration': 50,
        'app_sequence': ['housing_auction_4']},

        #Da
        {'name':'housing_auction_DA',
        'display_name': 'Housing Auction DA',
        'num_demo_participants': 6,
        # 'treatment_string':"['minimum_price','sellers_bid']",
        'treatment_string': "double_auction",
        'doc':"""Enter treatments to be played in session. Must be entered in
                 the form of a list []. Options are minimum_price, sellers_bid, double_auction. 
                 Treatments are played in order entered.""",
        'timeout_duration': 32,
        'complete_info': True,
        'app_sequence': ['housing_auction_4']},
]

# ROOM Settings for lab experiments

ROOM_DEFAULTS = {}

ROOMS = [
    {
        'name': 'ICES_lab',
        'display_name': 'ICES Experimental Economics Lab',
        'use_secure_urls': True,
        'participant_label_file': 'participants.txt'
    },
    {
        'name': 'econ831',
        'display_name': 'Econ 831 class',
        'participant_label_file': 'econ831.txt',
    },
    {
        'name': 'testfest',
        'display_name': 'Test Fest Rm 5025',
        'participant_label_file': 'numbers.txt',
    },
    {
        'name': 'online',
        'display_name': 'Online Lab',
        'use_secure_urls': True,
        'participant_label_file': 'online.txt'
    }
]

# anything you put after the below line will override
# oTree's default settings. Use with caution.
otree.settings.augment_settings(globals())
