import os, sys, random, hashlib

sys.dont_write_bytecode = True

from oauth import OAuthSignIn
from pprint import pprint

from config import *
from dbMgr import *
from ui import *

@app.route('/')
def index():

    if current_user.is_authenticated:
        return redirect('/curation')

    return render_template('login_fb.html')
    #return render_template('login.html')

@app.route('/download/<filename>.json', methods=['GET'])
def download(filename):

    filename = filename.split("_")
    print filename
    dumpCurationResults({filename[0]:[int(filename[1])]})
    
    root = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(directory=os.path.join(root,"exported"), filename=filename[0]+"_"+filename[1]+".json" )
    
def get_hexdigest(alg, salt, raw_password):
    if alg == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif alg == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")
    
def encrypt_password(raw_password):
    salt = get_hexdigest('sha1', str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest('sha1', salt, raw_password)
    return '%s$%s$%s' % ('sha1', salt, hsh)

def verify_password(enc_password, raw_password):
    algo, salt, hsh = enc_password.split('$')
    return hsh == get_hexdigest(algo, salt, raw_password)

def isValidAccount(email):
    file = open("emails.txt",'r')
    for line in file.readlines():
        if line.strip().lower() == email.lower():
            return True
    return False
    
def isRegistered(email):
    user = User.query.get(email)
    if user:
        return True
    else:
        return False
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('index'))
    
    '''
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # route for handling the login page logic
    if request.method == 'POST': 
    
        #print request.form
        
        if not request.form['uname']:
            rsp = "Username can't be blank. Please try again."
            return render_template('login.html',rsp=rsp)
        
        if not request.form['pw']:
            rsp = "Password can't be blank. Please try again."
            return render_template('login.html',rsp=rsp)
        
        # Decode input params
        userid = request.form['uname']
        #pw = bcrypt.hashpw(request.form['pw'].encode('utf-8'), bcrypt.gensalt())
        pw = encrypt_password(request.form['pw'].encode('utf-8'))
        
        # Find user from user database
        user = User.query.get(userid)
        
        # Verify password and log in
        if user and verify_password(user.password, request.form['pw'].encode('utf-8')):
            user.authenticated = True
            login_user(user, remember=True)
            return render_template('profile.html')
        else:
            if not user:
                rsp = "Incorrect user name. Please try again."
            else:
                rsp = "Incorrect password. Please try again."
            return render_template('login.html',rsp=rsp)
        
    return render_template('login.html')
    '''
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('login_fb.html')
    '''
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # route for handling the login page logic
    if request.method == 'POST': 
    
        #print request.form
        
        if not request.form['uname']:
            rsp = "User name can't be blank. Please try again."
            return render_template('register.html',rsp=rsp)
        
        if not request.form['pw']:
            rsp = "Password can't be blank. Please try again."
            return render_template('register.html',rsp=rsp)
        
        if not request.form['name']:
            rsp = "Name can't be blank. Please try again."
            return render_template('register.html',rsp=rsp)
        
        if not isValidAccount(request.form['uname']):
            rsp = "Email ID is not authorized, please contact admin."
            return render_template('register.html',rsp=rsp)
            
        if isRegistered(request.form['uname']):
            rsp = "Email ID is already registered, please login."
            return render_template('register.html',rsp=rsp)
        
        # Decode input params
        userid = request.form['uname']
        name = request.form['name']
        pw = encrypt_password(request.form['pw'].encode('utf-8'))
        #print userid, name, pw
        
        # Add to user database
        user = User(email=userid, password=pw)
        usrdb.session.add(user)
        usrdb.session.commit()
        
        # Add to curation database
        addCurator({"uid":userid,"name":name,"tags":[],"rating":5})
        
        rsp = "Account successfully registered."
        return render_template('register.html',rsp=rsp)
            
    return render_template('register.html')
    '''
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/curation')
@app.route('/v1/curation')
def show_curation():
    if current_user.is_authenticated:
        return render_template('curation.html')        
    else:
        return redirect(url_for('index'))

@app.route('/cards')
def cards():
    if current_user.is_authenticated:
        return render_template('cards.html')
    else:
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    
    if current_user.is_authenticated:
        return render_template('results.html',data=dumpCurationResults({"ulan":[3,4,5]}))
    else:
        return redirect(url_for('index'))

@app.route('/header')
def header():
    if current_user.is_authenticated:
        return render_template('header_search.html')
    else:
        return redirect(url_for('index'))

@app.route('/spec')
def show_specs():
    return render_template('spec.html',server=server[7:-1])
        
@app.route('/v1/spec')
def show_specs_v1():
    return render_template('spec.html')

@app.route('/profile')
def show_user_profile():
    if current_user.is_authenticated:
        return render_template('profile.html')
    return redirect('/login')

@app.route('/user')
def redirectUser():
    return redirect(url_for("user"))

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/stats')
def redirectStats():
    return redirect(url_for("stats"))
    
@app.route('/question')
def redirectQuestion():
    return redirect(url_for("question"))

@app.route('/answer/<option>')
def redirectAnswer(option):
    return redirect(url_for("answer")) + option

# Handle RESTful API for user services like  Registration/Login/Logout/Statistics
class userMgr(Resource):
    
    # Update User (Curator) profile. 
    def put(self):
        print "Input received: {} \n".format(request.json)
        
        if not current_user.is_authenticated:
            return {'status':"Couldn't authenticate user."}, 400
        
        if request.json == None:
            return {'message': 'No input provided'}, 400
        
        # Update tag for a user
        if 'tags' in request.json:
            #print request.json["tags"], type(request.json["tags"])
            if type(request.json["tags"]) != list:
                return {'message': 'Tags type should be list of String'}, 400
                
            tags = []
            for tag in request.json['tags']:
                # Temporary fix 
                if tag in museums.keys():
                    t = dbC[dname]["tag"].find_one({'tagname':tag.lower()})
                    if t == None:
                        message = 'tag with name <{}> does not exist'.format(tag)
                        return {'message': message}, 400
                    tags = tags + [t["_id"]]

            dbC[dname]["curator"].find_one_and_update({'uid':current_user.email},{'$set': {'tags':tags}})
        
        # Update name of a user
        if 'name' in request.json:
            #print request.json["name"], type(request.json["name"])
            if type(request.json["name"]) != str and type(request.json["name"]) != unicode:
                return {'message': 'Name type should by String'}, 400
            dbC[dname]["curator"].find_one_and_update({'uid':current_user.email},{'$set': {'name':request.json["name"]}})
        
        # Update rating of a user
        if 'rating' in request.json:
            #print request.json["name"], type(request.json["name"])
            if type(request.json["rating"]) != int:
                return {'message': 'Rating type should by integer'}, 400
            if request.json["rating"] > 5 or request.json["rating"] < 0:
                return {'message': 'Rating should be between 0-5 only'}, 400
            dbC[dname]["curator"].find_one_and_update({'uid':current_user.email},{'$set': {'rating':request.json["rating"]}})
        
        u = dbC[dname]["curator"].find_one({'uid':current_user.email},projection={'_id':False})
        
        return redirect(url_for('index'))
        #return {"username":u["uid"],"name":u["name"],"tags":getTags(u),"rating":u["rating"]}
    
    # Return user profile information
    def get(self):
        if not current_user.is_authenticated:
            return {'status':"Couldn't authenticate user."}, 400
        
        # getStats about all the questions answered by this user
        u = dbC[dname]["curator"].find_one({'uid':current_user.email},projection={'_id':False})
        answers = dbC[dname]["answer"].find({'author':current_user.email})
        
        # Initialize per museum stats 
        stats = {}
        for tag in museums.keys():
            stats[tag] = {"matched":0,"unmatched":0,"no-conclusion":0}
        
        for a in answers:
            # find question and check its current status 
            q = dbC[dname]["question"].find_one({'_id':ObjectId(a['qid'])})
            
            for tag in q['tags']:
                tag = dbC[dname]["tag"].find_one({'_id':ObjectId(tag)})['tagname']
                if q['status'] == statuscodes["Agreement"]:
                    stats[tag]["matched"] += 1
                elif q['status'] == statuscodes["Disagreement"]:
                    stats[tag]["unmatched"] += 1
                elif q['status'] == statuscodes["Non-conclusive"]:
                    stats[tag]["no-conclusion"] += 1

        return {"username":u["uid"],"name":u["name"],"tags":getTags(u),"rating":u["rating"],'progress':stats}
    
class User(UserMixin, usrdb.Model):
    __tablename__ = 'users'
    
    #id = usrdb.Column(usrdb.Integer, primary_key=True)
    #social_id = usrdb.Column(usrdb.String(64), nullable=False, unique=True)
    email = usrdb.Column(usrdb.String, primary_key=True)
    authenticated = usrdb.Column(usrdb.Boolean, default=False)
    password = usrdb.Column(usrdb.String)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated
        
    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

@lm.user_loader
def load_user(userid):
    return User.query.get(userid)

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, email, name = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        print ("Created new user\n")
        user = User(email=email)
        usrdb.session.add(user)
        usrdb.session.commit()
        addCurator({"uid":email,"name":name,"tags":[],"rating":5})
        
    login_user(user, True)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('index'))
    
# Handle RESTful API for getting data about link verifications
class dataMgr(Resource):
    
    def get(self):
        print "Input received: {} \n".format(request.args)
        
        if not current_user.is_authenticated:
            return {'status':"Couldn't authenticate user."}, 400
            
        stats = {}
        for tag in museums.keys():
            stats[tag] = {"matched":museums[tag]['matchedQ'],"unmatched":museums[tag]['unmatchedQ'],"no-conclusion":museums[tag]['unconcludedQ'],"Total":museums[tag]['totalQ']}
            
        return stats
    
# Handle RESTful API for getting/submitting questions
class questMgr(Resource):
    
    # Create questions from dedupe provided pairs, 
    # deprecated as questions are loaded from matched data dumped in json from record linkage program like dedupe or silk.
    def post(self):
        print "Input received: {} \n".format(request.json)
        
        if request.json == None:
            return {'message': 'No input provided'}, 400
        else:
            return createQuestionsFromPairs(request.json)
    
    # Retrieve set of questions and send it as a response
    def get(self):
        #print "Input received: {} \n".format(request.get_json())    
        #print "Input received: {} \n".format(request.json)
        #print "Input received: {} \n".format(request.data)
        print "Input received: {} \n".format(request.args)
        
        if not current_user.is_authenticated:
            return {'status':"Couldn't authenticate user."}, 400

        if request.args.get('count') == None:
            count = 10
        else:
            count = int(request.args.get('count'))
        
        if request.args.get('stats') == None:
            stats = False
        else:
            if request.args.get('stats').lower() == 'true':
                stats = True
            else:
                stats = False

        qs = getQuestionsForUser(count,stats)
        #pprint(qs)
        return qs
    
# Handle RESTful API for submitting answer
class ansMgr(Resource):
    
    def put(self):
        print "Input received: {} \n".format(request.json)
        
        if not current_user.is_authenticated:
            return {'status':"Couldn't authenticate user."}, 400
        
        if request.json == None:
            return {'status': 400, 'message': 'No input provided'}
        
        # Input validation
        if not 'comment' in request.json:
            a_comment = "No Comment Provided"
        else:
            a_comment = request.json['comment']
            
        if not 'value' in request.json:
            return {'message': 'value not provided with ther request'}, 400
        if not 'qid' in request.json:
            return {'message': 'qid not provided with ther request'}, 400
        
        a_value = request.json['value']
        
        if a_value not in [1,2,3] :
            return {'message': 'value should be either 1 (Yes) or 2 (No) or 3 (Not Sure) '}, 400
        
        qid = request.json['qid']
        uid = current_user.email
        answer = {"value":a_value,"comment":a_comment,"author":uid,"qid":qid}
        
        rsp = submitAnswer(qid,answer,uid)
        if rsp["status"] == False:
            return {'message':rsp["message"]},400
        else:
            return {'message':rsp["message"]}

# Rest API endpoints (V1)
api.add_resource(dataMgr, '/v1/stats',endpoint='stats')
api.add_resource(userMgr, '/v1/user',endpoint='user')
api.add_resource(questMgr, '/v1/question',endpoint='question')
api.add_resource(ansMgr, '/v1/answer',endpoint='answer')
    
def createQuestionsFromPairs(jsonData):
    bulkOutput = []
    for i in range(0,jsonData['count']):
        payload = jsonData['payload'][i]
        #print "\n Processing payload: ",payload
        if not 'uri1' in payload:
            return {'message': 'uri1 not provided with the request'}, 400
        if not 'uri2' in payload:
            return {'message': 'uri2 not provided with the request'}, 400
        if not 'dedupe' in payload:
            return {'message': 'dedupe not provided with the request'}, 400
        
        uri1 = payload['uri1']
        uri2 = payload['uri2']
        dedupe = payload['dedupe']
        
        decision = addOrUpdateQuestion(uri1,uri2,dedupe)
        #printDatabase("question")
        
        output = {"Value":[],"Comment":[]}
        if decision != None:
            # Iterate over decision documents and send various comments and actual answer
            for aid in decision:
                a = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
                output["Value"] = output["Value"]+[a["value"]]
                output["Comment"] = output["Comment"]+[a["comment"]]
                bulkOutput = bulkOutput+[output]
        else:
            bulkOutput = bulkOutput+[output]
    return bulkOutput

# Get question and related fields in nicer format for current user
def getQuestionsForUser(count,stats):
    # current user
    uid = current_user.email
    
    # Get questions
    questions = getQuestionsForUID(uid, count)
    
    # Get matching and non matching fields based on config file and sparql queries
    if questions != None:
        return populateQuestionsWithFields(questions, stats)
    else:
        return {'status':"Couldn't retrieve questions mostly because user not found."}, 400

# For every question, query sparql endpoint based on queries defined in config file
def populateQuestionsWithFields(questions, stats):
    
    output = []
    for question in questions:
    
        # Based on uri ordering, get properties 
        if checkURIOrdering(question['uri1'],question['uri2']):
            left = retrieveProperties(question['uri1'])
            right = retrieveProperties(question['uri2'])
        else:
            left = retrieveProperties(question['uri2'])
            right = retrieveProperties(question['uri1'])
        
        #print "\nLeft\n  "
        #pprint(left)
        #print "\nRight\n "
        #pprint(right)
        
        matches = getMatches(left, right)
        #print "\nmatches :\n"
        #pprint(matches)
        
        t = getTags(question)
        if stats == True:
            s = getStats(question)
            output += [{'qid': str(question['_id']),"ExactMatch":matches["ExactMatch"],"Unmatched":matches['Unmatched'],"tags":t,"stats":s}]
        else:
            output += [{'qid': str(question['_id']),"ExactMatch":matches["ExactMatch"],"Unmatched":matches['Unmatched'],"tags":t}]
        
        #print output
    return output

        
if __name__ == '__main__':
    
    # Initialize mongo db
    db_init()
    
    # Start the app
    if devmode: 
        #app.run(threaded=True,debug=True)
        app.run(debug=True)
    else:
        #app.run(threaded=True,debug=False)
        app.run(debug=False)