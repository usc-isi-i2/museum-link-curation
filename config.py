from flask import Flask, render_template, request, url_for, jsonify, redirect, flash, jsonify, Response, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user,current_user, login_required
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
from unidecode import unidecode
import os, json, sys, getopt

devmode = True

if devmode:
    server = "http://localhost:5000/"
    dbC = MongoClient('localhost', 27017)
else:
    server = "http://linking.americanartcollaborative.org/"
    dbC = MongoClient('localhost', 12345)

# Flask configuration
app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# restful, usrdb and login_manager instance
api = Api(app)

usrdb = SQLAlchemy(app)

lm = LoginManager(app)
lm.login_view = 'index'
lm.session_protection = 'strong'

confidenceLevel = 1
dname = "linkVerification"

def append_default_dict(x):
    z = x.copy()
    # Default values, these are updated after importing config and questions
    y = {"confidenceYesNo":2,"confidenceNotSure":2,"matchedQ":0,"unmatchedQ":0,"unconcludedQ":0,"totalQ":0}
    z.update(y)
    return z

# Every museum is dictionary is defined by tag name as key and value is array containing:
# Format: <URI identifier>, <ranking for ordering - alphabetical>, <confedenceLevel yes/no - default 2>, <confedenceLevel not sure default 2>, 
    #   <matched>, <unmatched>, <total questions>
museums = {#"aaa":append_default_dict({"uri":"/aaa/","ranking":1,"name":"Archives of American Art"}),
           #"aac":append_default_dict({"uri":"/aac/","ranking":2,"name","Asian Arts Council"}),
           #"aat":append_default_dict({"uri":"/aat/","ranking":3,"name":"The Getty - Art and Architecture Thesaurus Online"}),
           "acm":append_default_dict({"uri":"/acm/","ranking":4,"name":"Amon Carter Museum of American Art"}),
           "autry":append_default_dict({"uri":"/autry/","ranking":5,"name":"Autry Museum of the American West"}),
           "cbm":append_default_dict({"uri":"data.crystalbridges.org/","ranking":6,"name":"Crystal Bridges Museum"}),
           "ccma":append_default_dict({"uri":"/ccma/","ranking":7,"name":"Colby College Museum of Art"}),
           #"dbpedia":append_default_dict({"uri":"/dbpedia.org/","ranking":8,"name":"Structured information from Wikipedia"}),
           "dma":append_default_dict({"uri":"/dma/","ranking":9,"name":"Dallas Museum of Art"}),
           "gm":append_default_dict({"uri":"/GM/","ranking":10,"name":"Gilcrease Museum"}),
           "ima":append_default_dict({"uri":"/ima/","ranking":11,"name":"Indianapolis Museum of Art"}),
           "npg":append_default_dict({"uri":"/npg/","ranking":12,"name":"National Portrait Gallery"}),
           "nmwa":append_default_dict({"uri":"/nmwa/","ranking":13,"name":"National Museum of Wildlife Art"}),
           "puam":append_default_dict({"uri":"/puam/","ranking":14,"name":"Princeton University Art Museum"}),
           "saam":append_default_dict({"uri":"/saam/","ranking":15,"name":"Smithsonian American Art Museum"}),
           "ulan":append_default_dict({"uri":"/ulan/","ranking":16,"name":"The Getty Research Institute - Union List of Artist Names"}),
           #"viaf":append_default_dict({"uri":"/viaf/","ranking":17,"name":"The Virtual International Authority File"}),
           "wam":append_default_dict({"uri":"data.thewalters.org/","ranking":18,"name":"The Walters Art Museum"}),
           #"ycba":append_default_dict({"uri":"/ycba/","ranking":19,"name":"Yale Center for British Art"}),
           }

statuscodes = {"NotStarted":1,"InProgress":2,"Agreement":3,"Disagreement":4,"Non-conclusive":5}

field_desc = {'uri':"URI", 'name': 'Name', 'byear': 'Birth Date', 'bplace': 'Birth Place', 
    'dyear':'Death Date', 'dplace': 'Death Place', 'gender': 'Gender', 'nationality': 'Nationality'}

rootdir = os.path.dirname(os.path.abspath(__file__))

# Load API keys from file
f = open("key.json",'r').read()
keys = json.loads(f)
if devmode:
    app.config['OAUTH_CREDENTIALS'] = keys['dev']
else:
    app.config['OAUTH_CREDENTIALS'] = keys['production']