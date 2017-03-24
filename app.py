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
        logging.info('Input received: {}'.format(request.form))
        
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
            return render_template('profile.html',museums=museums,server=server[:-1])
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
        logging.info('Input received: {}'.format(request.form))
        
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
        logging.info('{} {} {}'.format(userid, name, pw))
        
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

@app.route('/answer/<option>')
def redirectAnswer(option):
    return redirect(url_for("answer")) + option

# Handle RESTful API for user services like  Registration/Login/Logout/Statistics
class userMgr(Resource):
    
    # Update User (Curator) profile. 
    def put(self):
        #print "Input received: {} \n".format(request.json)
        logging.info('Input received: {}'.format(request.json))
        
        if not current_user.is_authenticated:
            return {'error':"Couldn't authenticate user."}, 400
        
        if request.json == None:
            return {'error': 'No input provided'}, 400
        
        # Update tag for a user
        if 'tags' in request.json:
            #print request.json["tags"], type(request.json["tags"])
            #logging.info("{}, {}".format(request.json["tags"], type(request.json["tags"])))
            if type(request.json["tags"]) != list:
                return {'error': 'Tags type should be list of String'}, 400
                
            tags = []
            for tag in request.json['tags']:
                # Temporary fix 
                if tag in museums.keys():
                    t = dbC[dname]["tag"].find_one({'tagname':tag.lower()})
                    if t == None:
                        message = 'tag with name <{}> does not exist'.format(tag)
                        return {'error': message}, 400
                    tags = tags + [t["_id"]]

            dbC[dname]["curator"].find_one_and_update({'uid':current_user.email},{'$set': {'tags':tags}})
        
        # Update name of a user
        if 'name' in request.json:
            #print request.json["name"], type(request.json["name"])
            logging.info("{], {}".format(request.json["name"], type(request.json["name"])))
            if type(request.json["name"]) != str and type(request.json["name"]) != unicode:
                return {'error': 'Name type should by String'}, 400
            dbC[dname]["curator"].find_one_and_update({'uid':current_user.email},{'$set': {'name':request.json["name"]}})
        
        # Update rating of a user
        if 'rating' in request.json:
            #print request.json["name"], type(request.json["name"])
            logging.info("{}, {}".format(request.json["name"], type(request.json["name"])))
            if type(request.json["rating"]) != int:
                return {'error': 'Rating type should by integer'}, 400
            if request.json["rating"] > 5 or request.json["rating"] < 0:
                return {'error': 'Rating should be between 0-5 only'}, 400
            dbC[dname]["curator"].find_one_and_update({'uid':current_user.email},{'$set': {'rating':request.json["rating"]}})
        
        u = dbC[dname]["curator"].find_one({'uid':current_user.email},projection={'_id':False})
        
        return {"username":u["uid"],"name":u["name"],"tags":getTags(u),"rating":u["rating"]}
    
    # Return user profile information
    def get(self):
        if not current_user.is_authenticated:
            return {'error':"Couldn't authenticate user."}, 400
        
        # getStats about all the questions answered by this user
        u = dbC[dname]["curator"].find_one({'uid':current_user.email},projection={'_id':False})
                    
        return {"username":u["uid"],"name":u["name"],"tags":getTags(u),"rating":u["rating"],'payload':museums,'keys':sorted(museums.keys())}
    
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
        #print "Created new user with email",email
        logging.info("Created new user with email : {}".format(email))
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
    
# Handle RESTful API for exporting curation results
@app.route('/export', methods=['PUT'])
def export():
    if request.method == 'PUT':
        #print "PUT Input received: {} \n".format(request.json)
        logging.info("PUT Input received: {}".format(request.json))
        
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        
        # call dump results which should create dump results into json file and save as results.json
        dumpCurationResults(request.json,None)
        
        return jsonify({})
    
# Handle RESTful API for getting/submitting questions
class questMgr(Resource):

    # Retrieve set of questions and send it as a response
    def get(self):
        #print "Input received: {} \n".format(request.args)
        logging.info("Input received: {}".format(request.args))
        
        if not current_user.is_authenticated:
            return {'error':"Couldn't authenticate user."}, 400

        if request.args.get('count') == None:
            count = 1
        else:
            count = int(request.args.get('count'))
        
        if request.args.get('stats') == None:
            stats = False
        else:
            if request.args.get('stats').lower() == 'true':
                stats = True
            else:
                stats = False

        return getQuestionsForUser(count,stats)
    
# Handle RESTful API for submitting answer
class ansMgr(Resource):
    
    def put(self):
        #print "Input received: {} \n".format(request.json)
        logging.info("Input received: {}".format(request.json))
        
        if not current_user.is_authenticated:
            return {'error':"Couldn't authenticate user."}, 400
        
        if request.json == None:
            return {'error': 'No input provided'}, 400
        
        # Input validation
        if not 'comment' in request.json:
            a_comment = "No Comment Provided"
        else:
            a_comment = request.json['comment']
            
        if not 'value' in request.json:
            return {'error': 'value not provided with ther request'}, 400
        if not 'qid' in request.json:
            return {'error': 'qid not provided with ther request'}, 400
        
        a_value = request.json['value']
        
        if a_value not in [1,2,3] :
            return {'error': 'value should be either 1 (Yes) or 2 (No) or 3 (Not Sure) '}, 400
        
        qid = request.json['qid']
        uid = current_user.email
        answer = {"value":a_value,"comment":a_comment,"author":uid,"qid":qid}
        
        rsp = submitAnswer(qid,answer,uid)
        if rsp["status"] == False:
            return {'error':rsp["message"]},400
        else:
            return {'error':rsp["message"]}

# Get question and related fields in nicer format for current user
def getQuestionsForUser(count,stats):
    # current user
    uid = current_user.email

    # Get questions
    questions,rsp = getQuestionsForUID(uid, count)
    
    # Get matching and non matching fields based on config file and sparql queries
    if questions != None and questions != []:
        q,rsp = populateQuestionsWithFields(questions, stats)
        if q != []:
            return q
        else:
            return {'error':rsp}, 400
    else:
        if questions == [] and rsp == "success":
            return []
        else:
            return {'error':rsp}, 400

# For every question, query sparql endpoint based on queries defined in config file
def populateQuestionsWithFields(questions, stats):
    
    output = []
    for question in questions:       
        left = retrieveProperties(question['uri1'])
        right = retrieveProperties(question['uri2'])

        # Sparql query failed, sparql endpoint is down for either ULAN or aac
        if left == None or right == None:
            return [], "Sparql Endpoint not responding"

        #logging.info(left)
        #pprint(left)
        #logging.info(right)
        #pprint(right)
        
        matches = getMatches(left, right)
        #logging.info(matches)
        #pprint(matches)
        
        if stats == True:
            s = getStats(question)
            output += [{'qid': str(question['_id']), "score":format(question["record linkage score"], '.3f'),
                "ExactMatch":matches["ExactMatch"],"Unmatched":matches['Unmatched'],"stats":s}]
        else:
            output += [{'qid': str(question['_id']), "score":format(question["record linkage score"], '.3f'),
                "ExactMatch":matches["ExactMatch"],"Unmatched":matches['Unmatched']}]
        
        #print output
        #logging.info(output)
    return output,"success"

        
if __name__ == '__main__':
    
    # Process command line options
    parser = OptionParser()
    parser.add_option("-d", "--reset_dataset", dest="reset_dataset", type="string",help="Reset all data sets (True/False)")
    parser.add_option("-u", "--reset_users", dest="reset_users", type="string", help="Reset all users (True/False)")

    resetD = False
    resetU = False
    (options, args) = parser.parse_args()
    if options.reset_dataset and options.reset_dataset.lower() == "true":
        resetD = True
    if options.reset_users and options.reset_users.lower() == "true":
        resetU = True
    
    # Initialize mongo db
    db_init(resetU, resetD)
    
    api.add_resource(userMgr, '/user', endpoint='user')
    api.add_resource(questMgr, '/question', endpoint='question')
    api.add_resource(ansMgr, '/answer', endpoint='answer')
    
    # Start the app
    app.run(threaded=True,debug=False) 
