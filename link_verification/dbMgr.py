import csv, datetime, json, os
from random import randint
from pprint import pprint
from bson.objectid import ObjectId
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
    updateConfig()
    #populateCurators()
    populateQuestions(False)
    populateEntities()
    
    pprint(museums)
    
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
                  dbC[dname]["tag"].find_one({'tagname':"saam"})['_id'] ],
          "rating":5}
    dbC[dname]["curator"].insert_one(ce)
    ce = {"uid":"ksureka@usc.edu",
          "name":"Karishma Sureka",
          "tags":[dbC[dname]["tag"].find_one({'tagname':"ulan"})['_id'],
                  dbC[dname]["tag"].find_one({'tagname':"saam"})['_id'] ],
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
    #dedupe , dict, data coming from dedupe 
    
# Populate default set of questions
def populateQuestions(sample):
    
    # Add sample data
    if sample:
        qe = {"status":statuscodes["NotStarted"],
              "uniqueURI":generateUniqueURI("http://vocab.getty.edu/ulan/500028092","http://edan.si.edu/saam/id/person-institution/1681"),
              "lastSeen": datetime.datetime.utcnow(),
              "tags":[dbC[dname]["tag"].find_one({'tagname':"ulan"})['_id'],
                      dbC[dname]["tag"].find_one({'tagname':"saam"})['_id'] ],
               "uri1":"http://vocab.getty.edu/ulan/500028092",
               "uri2":"http://edan.si.edu/saam/id/person-institution/1681",
               "decision": [], #Should be updated in submit answer
               "dedupe": {}
             }
        dbC[dname]["question"].insert_one(qe)
        
        qe = {"status":statuscodes["NotStarted"],
              "uniqueURI":generateUniqueURI("http://vocab.getty.edu/ulan/500020062","http://edan.si.edu/saam/id/person-institution/26558"),
              "lastSeen": datetime.datetime.utcnow(),
              "tags":[dbC[dname]["tag"].find_one({'tagname':"ulan"})['_id'],
                      dbC[dname]["tag"].find_one({'tagname':"saam"})['_id'] ],
               "uri1":"http://vocab.getty.edu/ulan/500020062",
               "uri2":"http://edan.si.edu/saam/id/person-institution/26558",
               "decision": [], #Should be updated in submit answer
               "dedupe": {}
             }
        dbC[dname]["question"].insert_one(qe)
    else:
        if devmode:
            #populateQuestionsFromCSV(os.path.join('data', 'sample.csv'))
            populateQuestionsFromJSON(os.path.join('data', 'questions','NPGmin.json'))
            populateQuestionsFromJSON(os.path.join('data', 'questions','SAAMmin.json'))
        else:
            #populateQuestionsFromJSON(os.path.join('data', 'questions','DBPedia_architect.json'))
            #populateQuestionsFromJSON(os.path.join('data', 'questions','DBPedia_artist.json'))
            #populateQuestionsFromJSON(os.path.join('data', 'questions','NPG.json'))
            #populateQuestionsFromJSON(os.path.join('data', 'questions','SAAM.json'))
            populateQuestionsFromJSON(os.path.join('data', 'questions','NPGmin.json'))
            populateQuestionsFromJSON(os.path.join('data', 'questions','SAAMmin.json'))
        
        dbC[dname]["question"].create_index([("uri1", ASCENDING)])
        dbC[dname]["question"].create_index([("uri2", ASCENDING)])
        dbC[dname]["question"].create_index([("tags", ASCENDING)])
        dbC[dname]["question"].create_index([("status", ASCENDING)])
        dbC[dname]["question"].create_index([("decision", ASCENDING)])
        dbC[dname]["question"].create_index([("dedupe", ASCENDING)])
        dbC[dname]["question"].create_index([("lastSeen",DESCENDING)])
    #printDatabase("question")

# Populate default set of questions from csv file
def populateQuestionsFromCSV(csvfname):
    with open(csvfname, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row in spamreader:
            if len(row) == 2:
                # Find tags
                tag0 = findTag(row[0])
                tag1 = findTag(row[1])
                
                # Build document
                qe = {"status":statuscodes["NotStarted"],
                      "uniqueURI":generateUniqueURI(row[0],row[1]),
                      "lastSeen": datetime.datetime.utcnow(),
                      "tags":[dbC[dname]["tag"].find_one({'tagname':tag0})['_id'],
                              dbC[dname]["tag"].find_one({'tagname':tag1})['_id'] ],
                       "uri1":row[0],
                       "uri2":row[1],
                       "decision": [], #Should be updated in submit answer
                       "dedupe": {}
                     }
                
                # Add document
                dbC[dname]["question"].insert_one(qe)
                
                # Update statistics
                museums[tag0]['totalQ'] += 1
                museums[tag1]['totalQ'] += 1
                
    #printDatabase("question")
    
def populateQuestionsFromJSON(filename):
    json_data=open(filename).read()
    data = json.loads(json_data)
    count = data["count"]
    data = data["payload"]
    
    for i in range(0,count):
        #pprint(data[i])
        
        # Find tags
        tag0 = findTag(data[i]["uri1"])
        tag1 = findTag(data[i]["uri2"])
        
        # Build document
        qe = {"status":statuscodes["NotStarted"],
          "uniqueURI":generateUniqueURI(data[i]["uri1"],data[i]["uri2"]),
          "lastSeen": datetime.datetime.utcnow(),
          "tags":[dbC[dname]["tag"].find_one({'tagname':tag0})['_id'],
                  dbC[dname]["tag"].find_one({'tagname':tag1})['_id'] ],
           "uri1":data[i]["uri1"],
           "uri2":data[i]["uri2"],
           "decision": [], #Should be updated in submit answer
           "dedupe": data[i]["dedupe"]
        }
         
        # Add Document
        dbC[dname]["question"].insert_one(qe)
        
        # Update Statistics
        museums[tag0]['totalQ'] += 1
        museums[tag1]['totalQ'] += 1
     
    print ("Populated {} questions from {}.".format(count,filename))
    #printDatabase("question")

def populateEntities():
    if devmode:
        #populateEntitiesFromJSON(os.path.join('data', 'sample.json'))
        #updateEntitiesFromJSON(os.path.join('data', 'sampleUpdate.json'))
        #updateEntitiesFromJSON(os.path.join('data', 'sample.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','NPGmin.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','ULANmin_NPG.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','SAAMmin.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','ULANmin_SAAM.json'))
    else:
        #populateEntitiesFromJSON(os.path.join('data', 'entities','DBPedia_architect.json'))
        #populateEntitiesFromJSON(os.path.join('data', 'entities','DBPedia_artist.json'))
        #populateEntitiesFromJSON(os.path.join('data', 'entities','NPG.json'))
        #populateEntitiesFromJSON(os.path.join('data', 'entities','SAAM.json'))
        #populateEntitiesFromJSON(os.path.join('data', 'entities','ULAN.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','NPGmin.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','ULANmin_NPG.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','SAAMmin.json'))
        populateEntitiesFromJSON(os.path.join('data', 'entities','ULANmin_SAAM.json'))

    dbC[dname]["artists"].create_index([("@id", ASCENDING)])
    dbC[dname]["artists"].create_index([("tags", ASCENDING)])
    
#Entities
    #Schema as per Schema.org (Transformed by Yi Ding from different museum schema)
    
# Load artist entities fron json generated by dedupe input
def populateEntitiesFromJSON(filename):
    json_data=open(filename).read()
    data = json.loads(json_data)
    # Change this range on actual server
    for i in range(0,len(data["people"])):
        #pprint(data["people"][i])
        dbC[dname]["artists"].insert_one(data["people"][i])
    print ("Populated {} entities from {}".format(len(data["people"]),filename))
    #printDatabase("artists")

def updateEntitiesFromJSON(filename):
    json_data=open(filename).read()
    data = json.loads(json_data)
    # Change this range on actual server
    for i in range(0,len(data["people"])):

        uri = data["people"][i]["@id"]
        artist = dbC[dname]["artists"].find_one({'@id':uri},projection={'_id': False})

        # If there is no change than continue to next record
        if artist == data["people"][i]:
            continue
        
        # Update artist document with values from new input data
        for key in artist.keys():
            if key in data["people"][i]:
                artist[key] = data["people"][i][key]

        # Update artists collection 
        dbC[dname]["artists"].replace_one({'@id':uri}, artist )
        #print "\n Updated entities database with following entity\n"
        #pprint(artist)
    
    #printDatabase("artists")
    
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
        
def addOrUpdateQuestion(uri1,uri2,dedupe):
    uuri = generateUniqueURI(uri1,uri2)
    q = dbC[dname]["question"].find_one({'uniqueURI':uuri})
    
    # If uuri exists, ignore dedupe as this request is coming second time, just return decision
    if q != None:
        print "Question instance already exists\n"
        if q["decision"] == []:
            return None
        else:
            return q["decision"]
    # Create new question and add dedupe information as well
    else:
        qe = {"status":1,
              "uniqueURI":uuri,
              "lastSeen": datetime.datetime.utcnow(),
              "tags":[dbC[dname]["tag"].find_one({'tagname':findTag(uri1)})['_id'],
                      dbC[dname]["tag"].find_one({'tagname':findTag(uri2)})['_id'] ],
               "uri1":uri1,
               "uri2":uri2,
               "decision": [], #Should be updated in submit answer
               "dedupe ": dedupe 
             }
        status = dbC[dname]["question"].insert_one(qe).acknowledged
        
        if status:
            print 'Added question {}\n'.format(qe)
        
        return None
        
# Retrieve set of questions from database based on tags, lastseen, unanswered vs in progress
def getQuestionsForUID(uid,count):
    
    # If User with uid not present return error
    userOid = dbC[dname]["curator"].find_one({'uid':uid})
    if userOid == None or userOid['_id'] == None:
        print "User not found. \n"
        return None
    else:
        #print "Found uid's objectID ",userOid
        userTags = dbC[dname]["curator"].find_one({'uid':uid})['tags']
    
    # Filter-2: Questions list whose status is inProgress sorted as per lastSeen
    q2 = dbC[dname]["question"].find({"status":2}).sort([("lastSeen", DESCENDING)]).limit(5*count)
    
    q = []    
    # Filter-3: Remove questions that are already served to this user based on author (uid) in decision
    # Check every question whose status is in progress aka q2
    for question in q2:
        aids = question["decision"]
        
        answered = False
        
        # Check authors in all answers if current user has already answered the question
        for aid in aids:
            author = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
            if author and author["author"] == uid:
                answered = True
                break
        
        #Filter-4: Filter set of questions based on user and question tags
        tagPresent = False
        for tag in userTags:
            if tag in question["tags"]:
                tagPresent = True
                break
        
        # If question is not answered previously and tag is present, add it to set of question to be sent.
        if answered != True and tagPresent == True:
            q = q + [question]
    
    # Get not started questions only if started questions are not enough
    if len(q) < count:
        # Filter-1:  Questions list whose status is NotStarted sorted as per lastSeen 
        q1 = dbC[dname]["question"].find({"status":1}).sort([("lastSeen", DESCENDING)]).limit(5*count)

        # Append questions that are in NotStarted state
        for question in q1:
            #Filter-4: Filter set of questions based on user and question tags
            for tag in userTags:
                if tag in question["tags"]:
                    q = q + [question]
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

def getMatches(left,right):
    exactMatch = {"name":[],"value":[]}
    unmatched = {"name":["URI"],"lValue":[left["@id"]],"rValue":[right["@id"]]}
    
    fields = ["schema:name","schema:additionalName","schema:nationality","schema:birthDate","schema:deathDate","schema:birthPlace"]
    
    for field in fields:
        if field in left and field in right:
            # Basic Pre processing to help matching obvious values
            lVal = preProcess(left[field])
            rVal = preProcess(right[field])
            if lVal == rVal:
                exactMatch["name"] = exactMatch["name"]+[field]
                exactMatch["value"] = exactMatch["value"]+[lVal]
            else:
                unmatched["name"] = unmatched["name"]+[field]
                unmatched["lValue"] = unmatched["lValue"]+[left[field]]
                unmatched["rValue"] = unmatched["rValue"]+[right[field]]
        elif field in left:
            unmatched["name"] = unmatched["name"]+[field]
            unmatched["lValue"] = unmatched["lValue"]+[left[field]]
            unmatched["rValue"] = unmatched["rValue"]+[None]
        elif field in right:
            unmatched["name"] = unmatched["name"]+[field]
            unmatched["lValue"] = unmatched["lValue"]+[None]
            unmatched["rValue"] = unmatched["rValue"]+[right[field]]
    
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
    #author, String - uid of curator 
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
            author = dbC[dname]["answer"].find_one({'_id':ObjectId(aid)})
            if author and author["author"] == uid:
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
    
    # Create 
    for museum in args.keys():
        for status in args[museum]:
            # Create a file named museum_stauscode.json
            f = open("exported_"+museum+"_"+str(status)+".json",'w')
            out = {"count":0,"payload":[]}
            
            tid = dbC[dname]["tag"].find_one({'tagname':museum})['_id']
            questions = dbC[dname]["question"].find({'status':status})
            
            for q in questions:
                a = {}
                if tid in q['tags']:
                    a["dedupe"] = q["dedupe"]
                    a["uri1"] = q["uri1"]
                    a["uri2"] = q["uri2"]
                    temp = out["payload"]
                    temp.append(a)
                    out["payload"] = temp
                    out["count"] += 1
            
            # Dump the output in json file
            f.writelines(json.dumps(out,indent=4))
            
        
    results = {"matched":[],"unmatched":[]}
    
    # Get all the questions that are concluded successful
    questions = dbC[dname]["question"].find( {'$or': [{'status':3},{'status':4}]} )
    
    # Run loop over questions and populate uri(s) and yes/no votes
    for q in questions:
        rs = {"uri1":"","uri2":"","Yes":0,"No":0}
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
        
        if rs["Yes"] > rs["No"]:
            results["matched"].append(rs)
        else:
            results["unmatched"].append(rs)
    
    return results
