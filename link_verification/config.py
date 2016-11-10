from flask import Flask, render_template, request, url_for, jsonify, redirect, flash, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user,current_user, login_required
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
from unidecode import unidecode

devmode = True

if devmode:
    server = "http://localhost:5000/"
    dbC = MongoClient('localhost', 27017)
else:
    #server = "http://52.37.251.245/"
    #server = "http://ec2-52-37-251-245.us-west-2.compute.amazonaws.com/"
    server = "http://linking.americanartcollaborative.org/"
    dbC = MongoClient('localhost', 12345)

# Flask configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# restful, usrdb and login_manager instance
api = Api(app)
usrdb = SQLAlchemy(app)
lm = LoginManager(app)

lm.login_view = 'index'
lm.session_protection = 'strong'

confidenceLevel = 2
dname = "linkVerification"

def append_default_dict(x):
    z = x.copy()
    y = {"confidenceYesNo":2,"confidenceNotSure":2,"matchedQ":0,"unmatchedQ":0,"totalQ":0}
    z.update(y)
    return z

# Every museum is dictionary is defined by tag name as key and value is array containing:
# Format: <URI identifier>, <ranking for ordering - alphabetical>, <confedenceLevel yes/no - default 2>, <confedenceLevel not sure default 2>, 
    #   <matched>, <unmatched>, <total questions>
museums = {#"aaa":append_default_dict({"uri":"//","ranking":1}),
           #"aac":append_default_dict({"uri":"//","ranking":2}),
           #"aat":append_default_dict({"uri":"//","ranking":3}),
           #"acm":append_default_dict({"uri":"//","ranking":4}),
           "autry":append_default_dict({"uri":"theautry.org","ranking":5}),
           #"cbm":append_default_dict({"uri":"//","ranking":6}),
           #"ccma":append_default_dict({"uri":"//","ranking":7}),
           "dbpedia":append_default_dict({"uri":"/dbpedia.org/","ranking":8}),
           #"dma":append_default_dict({"uri":"//","ranking":9}),
           #"gm":append_default_dict({"uri":"//","ranking":10}),
           #"ima":append_default_dict({"uri":"//","ranking":11}),
           "npg":append_default_dict({"uri":"/npgConstituents/","ranking":12}),
           #"nmwa":append_default_dict({"uri":"//","ranking":13}),
           #"puam":append_default_dict({"uri":"//","ranking":14}),
           "saam":append_default_dict({"uri":"/saam/","ranking":15}),
           "ulan":append_default_dict({"uri":"/ulan/","ranking":16}),
           "viaf":append_default_dict({"uri":"/viaf/","ranking":17}),
           #"wam":append_default_dict({"uri":"//","ranking":18}),
           #"ycba":append_default_dict({"uri":"//","ranking":19}),
           }

statuscodes = {"NotStarted":1,"InProgress":2,"Agreement":3,"Disagreement":4,"Non-conclusive":5}

if devmode:
    app.config['OAUTH_CREDENTIALS'] = {
        'facebook': {
            'id': '622058264638304',
            'secret': '56bba85a0bef4cae8d07537701bbfe1f'
        }
    }
else:
    app.config['OAUTH_CREDENTIALS'] = {
        'facebook': {
            'id': '621200901380211',
            'secret': '0afb04701e956a3cf74ac876560e7041'
        }
    }
