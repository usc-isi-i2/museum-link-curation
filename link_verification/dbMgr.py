import csv, datetime, json, os
from random import randint
from pprint import pprint
from bson.objectid import ObjectId
from SPARQLWrapper import SPARQLWrapper, JSON
from config import *

# dbC and dname are mongoDb based database for entities and their curation data
def db_init():

    if devmode:
        usrdb.drop_all()
        usrdb.create_all()

        cleanDatabases()
        createDatabase()
        cleanDatabase("answer")
    else:
        if dbC[dname]["tag"].find_one() == None:
            usrdb.drop_all()
            usrdb.create_all()

            cleanDatabases()
            createDatabase()
            cleanDatabase("answer")
            print "Initialized databases\n"
    
    updateConfig()
    pprint(museums)
    #printDatabases()
    
# Print the database just to check current data
def printDatabases():
    print "\nPrinting ",dname," if it exists"
    for cname in dbC[dname].collection_names(include_system_collections=False):
        print "\nPrinting Collection ",cname
        for val in dbC[dname][cname].find():
            print " \n", val
        print "\n"

# Removes all the data from all tables of given database
def cleanDatabases():
    print "\nDropping database",dname,"if it exists"
    
    for cname in dbC[dname].collection_names(include_system_collections=False):
        print "\nDropping collection (aka database)",cname
        dbC[dname][cname].drop()
    print "\n"

# Print particular Document from a Collection
def printDatabase(docname):
    print "\nPrinting Collection ",docname
    for val in dbC[dname][docname].find():
        print " \n", val
    print "\n"
    
# Clean particular Document from a Collection
def cleanDatabase(docname):
    print "\nDropping collection (aka database)",docname
    for val in dbC[dname][docname].find():
        print "\nDropping: ",val
    dbC[dname][docname].delete_many({})
    dbC[dname][docname].drop()            
    print "\n"
            
# Create database with default values for curation
def createDatabase():
    populateTags()
    
    #populateCurators()
    populateQuestions()
    #populateEntities()
    
#Tag
    #tagname, string 

# Populate database with default tags
def populateTags():
    # Add all standard tags
    for key in museums.keys():
        te = {"tagname":key}
        dbC[dname]["tag"].insert_one(te)
    
    #printDatabase("tag") 
 
# Read config file and update various dynamic properties
def updateConfig():
    file = open("threshold.txt",'r')
    for line in file.readlines():
        inp = line.strip().lower().split(" ")
        if inp[0] in museums:
            museums[inp[0]]['confidenceYesNo'] = int(inp[1])
            museums[inp[0]]['confidenceNotSure'] = int(inp[2])
    
    #pprint(museums)
 
#Curator
    #uid, String - userID
    #name, String
    #rating, Integer
    #questionsSeen, List of object IDs from Question
    #tags, list of object IDs from Tags
    
# Populate database with default curators
def populateCurators():
    ce = {"uid":"nilayvac@usc.edu",
          "name":"Nilay Chheda",
          "tags":[dbC[dname]["tag"].find_one({'tagname':"ulan"})['_id'],
                  dbC[dname]["tag"].find_one({'tagname':"acm"})['_id'] ],
          "rating":5}
    dbC[dname]["curator"].insert_one(ce)

# Add the new curator from the client interface
def addCurator(ce):
    status = dbC[dname]["curator"].insert_one(ce).acknowledged
    if status:
        print 'Added curator {}\n'.format(ce)
    
# Question
    #status, integer: 1 - Not Started, 2 - In Progress, 3 - Completed, 4 - Disagreement
    #uniqueURI, String: alphabetical concatenation of two URI to get unique ID
    #lastSeen, datetime field to select question based on time it was asked to previous curator
    #tags, list of object IDs from Tags
    #uri1, for now, just a URI related to a specific artist
    #uri2, for now, just another URI related to same specific artist
    #decision, list of object IDs from Answer
    #similarity , dict, meta data about similarity algorithm and its output from record linkage
    
# Populate default set of questions
def populateQuestions():

    basedir = os.path.join("linkage", "questions")
    datasets = [d[:d.index('.')] for d in os.listdir(basedir)]
    
    for dataset in datasets:
        if dataset != "acm":
            continue
            
        f = dataset+'.json'
        f = os.path.join(rootdir,'linkage','questions',f)
        populateQuestionsFromJSON(f)
    
    dbC[dname]["question"].create_index([("uri1", ASCENDING)])
    dbC[dname]["question"].create_index([("uri2", ASCENDING)])
    dbC[dname]["question"].create_index([("tags", ASCENDING)])
    dbC[dname]["question"].create_index([("status", ASCENDING)])
    dbC[dname]["question"].create_index([("decision", ASCENDING)])
    dbC[dname]["question"].create_index([("similarity", ASCENDING)])
    dbC[dname]["question"].create_index([("lastSeen",DESCENDING)])
    #printDatabase("question")

# Populate default set of questions from json file
def populateQuestionsFromJSON(f):
    
    # Load questions
    questions = open(f)
    
    # Load all the questions into MongoDb
    count = 0
    for q in questions:
        
        # Convert string into json object
        q = json.loads(q)
        
        # Find tags
        tag0 = findTag(q["uri1"])
        tag1 = findTag(q["uri2"])
        
        # Build document
        qe = {"status":statuscodes["NotStarted"],
              "uniqueURI":generateUniqueURI(q["uri1"],q["uri2"]),
              "lastSeen": datetime.datetime.utcnow(),
              "tags":[dbC[dname]["tag"].find_one({'tagname':tag0})['_id'],dbC[dname]["tag"].find_one({'tagname':tag1})['_id'] ],
              "uri1":q["uri1"],
              "uri2":q["uri2"],
              "decision": [], # Should be updated in submit answer
              "similarity": q["similarity"]
        }
         
        # Add Document
        dbC[dname]["question"].insert_one(qe)
        count += 1
        
        # Update Statistics
        museums[tag0]['totalQ'] += 1
        museums[tag1]['totalQ'] += 1
     
    print ("Populated {} questions from {}.".format(count,f))
    #printDatabase("question")
    
#Find tag from the uri
def findTag(uri):
    for tag in museums.keys():
        if museums[tag]['uri'] in uri:
            return tag
    
    return "NoTag"
    
# Extract tag name list from tags object id for an entity
def getTags(entity):
    tags = []
    for tag in entity["tags"]:
        tags = tags + [dbC[dname]["tag"].find_one({'_id':ObjectId(tag)})["tagname"]]
    return tags

# Return true if uri1 ranks hire than uri2
def checkURIOrdering(uri1,uri2):
    for tag in museums.keys():
        if museums[tag]['uri'] in uri1:
            rank1 = museums[tag]['ranking']
        if museums[tag]['uri'] in uri2:
            rank2 = museums[tag]['ranking']

    if rank1 < rank2:
        return True
    else:
        return False
            
# Generate unique URI based on alphabetical ordering defined for different museums 
def generateUniqueURI(uri1,uri2):
    if checkURIOrdering(uri1,uri2):
        return uri1+uri2
    else:
        return uri2+uri1
        
def addOrUpdateQuestion(uri1,uri2,similarity):
    uuri = generateUniqueURI(uri1,uri2)
    q = dbC[dname]["question"].find_one({'uniqueURI':uuri})
    
    # If uuri exists, ignore linkage as this request is coming second time, just return decision
    if q != None:
        print "Question instance already exists\n"
        if q["decision"] == []:
            return None
        else:
            return q["decision"]
    # Create new question
    else:
        qe = {"status":1,
              "uniqueURI":uuri,
              "lastSeen": datetime.datetime.utcnow(),
              "tags":[dbC[dname]["tag"].find_one({'tagname':findTag(uri1)})['_id'],
                      dbC[dname]["tag"].find_one({'tagname':findTag(uri2)})['_id'] ],
               "uri1":uri1,
               "uri2":uri2,
               "decision": [], #Should be updated in submit answer
               "similarity ": similarity 
             }
        status = dbC[dname]["question"].insert_one(qe).acknowledged
        
        if status:
            print 'Added question {}\n'.format(qe)
        
        return None
        
# Retrieve set of questions from database based on tags, lastseen, unanswered vs in progress
def getQuestionsForUID(uid,count):
    
    # If User with uid not present return error, otherwise get tags for user
    userOid = dbC[dname]["curator"].find_one({'uid':uid})
    if userOid == None or userOid['_id'] == None:
        print "User not found. \n"
        return None
    else:
        #print "Found uid's objectID ",userOid
        userTags = dbC[dname]["curator"].find_one({'uid':uid})['tags']
    
    if userTags == []:
        print "User does not have any tags associated with their profile. \n"
        return []
    
    # Questions to be served...
    q = []
    
    # Filter-1: Get questions whose status is inProgress sorted as per lastSeen
    #q2 = dbC[dname]["question"].find({"status":statuscodes['InProgress']}).sort([("lastSeen", DESCENDING)]).limit(5*count)
    q1 = dbC[dname]["question"].find({"status":statuscodes['InProgress']}).sort([("lastSeen", DESCENDING)])
    
    # Filter-2: Remove questions that are already served to this user
    for question in q1:
        aids = question["decision"]
        
        answered = False
        
        # Check authors in all answers if current user has already answered the question
        for aid in aids:
            author = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
            if author and author["author"] == uid:
                answered = True
                break
        
        #Filter-3: Filter set of questions based on matching tags
        tagPresent = False
        for tag in userTags:
            if tag in question["tags"]:
                tagPresent = True
                break
        
        # Question is inProgress, not answered by this user and matches the tag -> save it.
        if answered != True and tagPresent == True:
            q = q + [question]
            
            # Break out if number of questions match the requested count
            if len(q) == count:
                break
    
    # Get not started questions only if started questions are not enough
    if len(q) < count:
        # Filter-1: Get questions whose status is NotStarted sorted as per lastSeen
        #q1 = dbC[dname]["question"].find({"status":statuscodes['NotStarted']}).sort([("lastSeen", DESCENDING)]).limit(5*count)
        q2 = dbC[dname]["question"].find({"status":statuscodes['NotStarted']}).sort([("lastSeen", DESCENDING)])

        #Filter-2: Filter set of questions based on matching tags
        for question in q2:
        
            tagPresent = False
            for tag in userTags:
                if tag in question["tags"]:
                    tagPresent = True
                    break
            
            # Question is inProgress, not answered by this user and matches the tag -> save it.
            if tagPresent:
                q = q + [question]
            
                # Break out if number of questions match the requested count
                if len(q) == count:
                    break

    q_new = []
    # Update lastSeen for all questions that are being returned
    for question in q:
        qid = question['_id']
        q_new += [ dbC[dname]["question"].find_one_and_update(
            {'_id':ObjectId(qid)},
            {'$set': {'lastSeen':datetime.datetime.utcnow()}},
            return_document=ReturnDocument.AFTER) ]
            
    return q_new

# Basic Pre processing to help matching obvious values
def preProcess(value):
    
    #print "Pre processing : "+str(value)+" with type : "+str(type(value))
    
    if type(value) == str or type(value) == int or type(value) == unicode:
        # First convert int to strings
        if type(value) == int:
            value = str(value)

        # Remove leading and trailing whitespace 
        value = value.strip()

        # Covert to ASCII just for the comparison
        value = unidecode(value)
    
    #print "Pre processed : "+str(value)+" with type : "+str(type(value))

    return value

def retrieveProperties(uri):

    if '/ulan/' in uri: 
        f = open('ulan.sparql','r')
        sparql = SPARQLWrapper('http://vocab.getty.edu/sparql')
    else:
        f = open('aac.sparql','r')
        sparql = SPARQLWrapper('http://data.americanartcollaborative.org/sparql')
    
    sparql.setQuery(f.read().replace('???',uri))
    sparql.setReturnFormat(JSON)
    
    rs = sparql.query().convert()
    rs = rs['results']['bindings'][0]
    
    data = {}
    for key in rs.keys():
        data[key] = rs[key]['value']

    f.close()
    return data
    
def getMatches(left,right):
    # output format
    exactMatch = {"name":[],"value":[]}
    
    unmatched = {"name":["URI"],"lValue":[left["uri"]],"rValue":[right["uri"]], "leftT":findTag(left["uri"]), "rightT":findTag(right["uri"])}
    
    for field in right.keys():
        # URI are not going to match 
        if field == 'uri':
            continue
        if field in left.keys() and field in right.keys():
            
            # Basic Pre processing to help matching obvious values
            lVal = preProcess(left[field])
            rVal = preProcess(right[field])
            
            if lVal == rVal:
                exactMatch["name"].append(field_desc[field])
                exactMatch["value"].append(lVal)
            else:
                unmatched["name"].append(field_desc[field])
                unmatched["lValue"].append(left[field])
                unmatched["rValue"].append(right[field])
        elif field in left:
            unmatched["name"].append(field_desc[field])
            unmatched["lValue"].append(left[field])
            unmatched["rValue"].append(None)
        elif field in right:
            unmatched["name"].append(field_desc[field])
            unmatched["lValue"].append(None)
            unmatched["rValue"].append(right[field])
    
    return {"ExactMatch":exactMatch,"Unmatched":unmatched}

def getStats(q):
    noNo = 0
    noYes = 0
    noNotSure = 0
    for aid in q['decision']:
        a = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
        if a != None:
            if a["value"] == 1:
                noYes = noYes + 1
            elif a["value"] == 2:
                noNo = noNo + 1
            elif a["value"] == 3:
                noNotSure = noNotSure + 1

    #print 'Yes is {}, No is {}, Undecided is {} \n'.format(noNo,noYes,noNotSure)
    return {"Yes":noYes,"No":noNo,"Not Sure":noNotSure}
    
#Answer
    #value, Integer value - 1 - Yes, 2 - No, 3 - Not Sure
    #comment, String optional 
    #author, String - uid of curator (email)
    #qid, question id this answer belong to
def submitAnswer(qid, answer, uid):
    
    # from qid retrieve question 
    q = dbC[dname]["question"].find_one({'_id':ObjectId(qid)})
    
    if q == None:
        #print "Submit answer failed for qid: ", qid
        message = "Question not found for qid: {}".format(qid)
        return {"status":False,"message":message}
    elif q['status'] == statuscodes["Agreement"] or q['status'] == statuscodes["Disagreement"] or q['status'] == statuscodes["Non-conclusive"]:
        #print "Question has already been answered by prescribed number of curators, qid: ", qid
        message = "Predetermined number of curators have already answered question with qid {}".format(qid)
        return {"status":False,"message":message}
    else:
        #print "Found the question"
        
        #Check if user has already answered the question
        # Check authors in all answers if current user has already answered the question
        for aid in q["decision"]:
            answer = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
            if answer and answer["author"] == uid:
                #print "User has already submitted answer to question ", qid
                message = "User has already submitted answer to question with qid {}".format(qid)
                return {"status":False,"message":message}
        
        a = dbC[dname]["answer"].insert_one(answer)
        aid = a.inserted_id
        if a.acknowledged:
            print 'Added answer {}\n'.format(answer)
        
        # update decision with answer object id
        q['decision'] = q['decision']+[aid]
        #print "decision is: ", q['decision']
        
        # retrieve all answers
        noYes = 0
        noNo = 0
        noNotSure = 0
        
        #printDatabase("answer")
        
        for aid in q['decision']:
            a = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
            if a != None:
                if a["value"] == 1:
                    noYes = noYes + 1
                elif a["value"] == 2:
                    noNo = noNo + 1
                elif a["value"] == 3:
                    noNotSure = noNotSure + 1
        
        # Update status of the question based on different answers
        
        # Find tags associated with question
        tags = []
        for tagid in q['tags']:
            tags.append(dbC[dname]["tag"].find_one({'_id':ObjectId(tagid)})['tagname'])
    
        # Get confidence level for a particular museum
        for tag in tags:
            if tag != "ulan":
                confidenceYesNo = museums[tag]['confidenceYesNo']
                confidenceNotSure = museums[tag]['confidenceNotSure']
    
        #print "current Y/N/NA: ",noYes,noNo,noNotSure
        #print "confidence Y-N/NA: ",confidenceYesNo,confidenceNotSure
    
        if noYes == confidenceYesNo:
            q['status'] = statuscodes["Agreement"] # Update to, Agreement 
            # Update linked statistics for tags of question submitted
            for tag in tags:
                museums[tag]['matchedQ'] += 1
        elif noNo == confidenceYesNo:
            q['status'] = statuscodes["Disagreement"] # Update to, Disagreement 
            # Update linked statistics for tags of question submitted
            for tag in tags:
                museums[tag]['unmatchedQ'] += 1
        elif noNotSure == confidenceNotSure:
            q['status'] = statuscodes["Non-conclusive"] # Update to, Non conclusive 
            for tag in tags:
                museums[tag]['unconcludedQ'] += 1
        else:
            q['status'] = statuscodes["InProgress"] # Update to, InProgress
    
        #update database entry of question with new status and decision
        q =  dbC[dname]["question"].find_one_and_update(
            {'_id':ObjectId(qid)},
            {'$set': {'status':q['status'],'decision':q['decision']}},
            #projection={'_id':False,'status':True},
            return_document=ReturnDocument.AFTER)
        
        print "Updated question document {}\n".format(q)
        #printDatabase("answer")
        return {"status":True,"message":"Appended answer to question's decision list"}

# museum - array of museum tags to retrieve , # status - array of different status codes to be retrieved
# Parameter format: {"museum tag":[status codes...],...}
def dumpCurationResults(args):
    # Create file handle
    f = open(os.path.join(rootdir,"results.json"),'w')
    out = {"count":0,"payload":[]}
    
    for museum in args['data']['tags']:
        statuses = []
        
        if museum in args['data']['s3']:
            statuses.append(statuscodes['Agreement'])
        if museum in args['data']['s4']:
            statuses.append(statuscodes['Disagreement'])
        if museum in args['data']['s5']:
            statuses.append(statuscodes['Non-conclusive'])
        
        # Find questions with museum as a tag and a particular status
        print museum, statuses
        for status in statuses:
        
            tid = dbC[dname]["tag"].find_one({'tagname':museum})['_id']
            questions = dbC[dname]["question"].find({'status':status})
            
            for q in questions:
                a = {}
                if tid in q['tags']:
                    a["similarity"] = q["similarity"]
                    a["uri1"] = q["uri1"]
                    a["uri2"] = q["uri2"]
                    temp = out["payload"]
                    temp.append(a)
                    out["payload"] = temp
                    out["count"] += 1
            
    # Dump the output in json file
    f.writelines(json.dumps(out,indent=4))

def returnCurationResults():
    results = {"matched":[],"unmatched":[]}
    
    # Get all the questions that are concluded successful
    questions = dbC[dname]["question"].find( {'$or': [{'status':statuscodes['Agreement']},{'status':statuscodes['Disagreement']},{'status':statuscodes['Non-conclusive']}] } )
    
    # Run loop over questions and populate uri(s) and yes/no votes
    for q in questions:
        rs = {"uri1":"","uri2":"","Yes":0,"No":0,"notSure":0}
        rs["uri1"] = q["uri1"]
        rs["uri2"] = q["uri2"]
        
        # Calculate yes/no votes
        noYes = 0
        noNo = 0
        noNotSure = 0
        for aid in q['decision']:
            a = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
            if a != None:
                if a["value"] == 1:
                    noYes = noYes + 1
                elif a["value"] == 2:
                    noNo = noNo + 1
                elif a["value"] == 3:
                    noNotSure = noNotSure + 1
    
        rs["Yes"] = noYes
        rs["No"] = noNo
        rs["notSure"] = noNotSure
        
        if rs["Yes"] > rs["No"]:
            results["matched"].append(rs)
        else:
            results["unmatched"].append(rs)
            
    return results
