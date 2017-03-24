'''
Linking records of various aac affiliated museums against ULAN museum.
Record blocking using birth year and record linkage string comparison algorithms
'''

import sys, os, re, json, time
from unidecode import unidecode
from pprint import pprint
import pkg_resources
from optparse import OptionParser

class recordLinkage:

    basedatabase = "ulan"
    basedir = 'dataset'
    #get topN matches
    topN = 3
    #block first N characters
    firstN = 2
    absdir = os.path.dirname(os.path.realpath(__file__))
    
    def __init__(self,base):
        self.basedatabase = base

    #Checks if firstN characters of name match; extract all space separated tokens from the name
    def check_name_match(self, museum_author_name, ulan_name):
        if isinstance(ulan_name, unicode):
            a = unidecode(ulan_name)
        else:
            a = unidecode(unicode(ulan_name.decode('unicode-escape').encode('utf-8'),'utf-8')).strip().lower()
        if isinstance(museum_author_name, unicode):
            b = unidecode(museum_author_name)
        else:
            b = unidecode(unicode(museum_author_name.decode('unicode-escape').encode('utf-8'),'utf-8')).strip().lower()

        #print(a,b)
        # Keep only alpha numerics
        a = re.sub('[^A-Za-z0-9 ]+', '', a)
        b = re.sub('[^A-Za-z0-9 ]+', '', b)

        #extract all space separated tokens from the names
        tk_a = a.split(' ')
        tk_b = b.split(' ')

        for t1 in tk_a:
            for t2 in tk_b:
                if t1[:self.firstN] == t2[:self.firstN]:
                    return True

        return False

    def v1Matching(self, ulanentity, entity):
        # Check if ulan entity birth year belong to any of the block keys.
        #print(ulanentity)
        
        linkage = {"match":False}
        
        if 'byear' in entity: 
            if self.preprocessBirth(ulanentity['byear']['value']) == self.preprocessBirth(entity['byear']['value']):
                # do string similarity
                linkage = self.matchNames(ulanentity['name']['value'], entity['name']['value'],'hj', 0.8)
                
        # If threshold was met
        if linkage['match']:
            return {"id1":entity['uri']['value'],
                    "id2":ulanentity['uri']['value'],
                    "record linkage score":linkage["score"],
                    "human curated":False,
                    "linkage":{}}
        else:
            return None
            

    #default check first 2 characters of the last name before matching Names
    def v2Matching(self, ulanentity, entity, k=2):
    
        ulan_author_name = ulanentity['name']['value']
        museum_author_name = entity['name']['value']
        
        linkage = {"match":False}
        
        name_blocking_match = self.check_name_match(museum_author_name, ulan_author_name)
        if name_blocking_match:
            # do string similarity
            linkage = self.matchNames(ulanentity['name']['value'], entity['name']['value'],'hj', 0.9)

        if linkage['match']:
            return {"id1":entity['uri']['value'],
                    "id2":ulanentity['uri']['value'],
                    "record linkage score":linkage["score"],
                    "human curated":False,
                    "linkage":{}}
        else:
            return None
                
    # Run record linkage against base database with blocking on birth year
    def findPotentialMatches(self, d, output_folder):
        if d:
            datasets = d.split()
        else:
            # Create list of all datasets available
            datasets = [dname[:dname.index('.')] for dname in os.listdir(self.basedir)]
        
        output_dir = os.path.join(self.absdir, output_folder)

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as exc: # Guard against race condition
                raise
        
        # Iterate over all datasets
        for dname in datasets:
            # Skip ulan 
            if dname == self.basedatabase:
                continue

            print "Analyzing ",dname
                
            start_time = time.time()

            # Open output file
            out = open(os.path.join(self.absdir, output_folder, dname+".json"),'w')
                
            # Open dataset file and ulan file 
            entities = open(os.path.join(self.absdir,self.basedir,dname+".json"))
            
            # Record blocking + Record Linkage
            for entity in entities:
                # convert line read into json
                entity = json.loads(entity)
                potential_matches = []
                
                ulanentities = open(os.path.join(self.absdir,self.basedir,self.basedatabase+".json"))
                current_matches = set()
                for ulanentity in ulanentities:
                    # convert line read into json
                    ulanentity = json.loads(ulanentity)
                    '''
                        Get matches by both blocking by birth year and name blocking of first 2 characters
                        Add threshold to take the topN matches

                        v1 blocks on birthyear
                        v2 blocks on firstN characters
                    '''
                    match_v1 = self.v1Matching(ulanentity, entity)
                    if match_v1:
                        match_v1['linkage']['ulan_name'] = ulanentity['name']['value']
                        match_v1['linkage']['museum_name']  = entity['name']['value']
                        if match_v1['id2'] not in current_matches:
                            potential_matches.append(match_v1)
                            current_matches.add(match_v1['id2'])

                    match_v2 = self.v2Matching(ulanentity, entity)
                    if match_v2:
                        match_v2['linkage']['ulan_name'] = ulanentity['name']['value']
                        match_v2['linkage']['museum_name']  = entity['name']['value']
                        if match_v2['id2'] not in current_matches:
                            potential_matches.append(match_v2)
                            current_matches.add(match_v2['id2'])


                # Close ULAN entities file handle
                ulanentities.close()
                # Sort potential matches based on matching score and select top N
                potential_matches = sorted( potential_matches ,key=lambda x: x['record linkage score'],reverse=True )
                perfactMatch = False
                for i in range(0,self.topN):
                    
                    # Break if no potential matches 
                    if len(potential_matches) == 0:
                        #print "No matches were found for entity", entity
                        break
                        
                    # Break if not enough potential matches 
                    elif len(potential_matches)-1 < i:
                        #print "Enough matches were not found for entity", entity
                        break
                        
                    elif perfactMatch and potential_matches[i]['record linkage score'] < 1:
                        #print "Found all perfect matched for entity ", entity
                        break

                    out.write(json.dumps(potential_matches[i]))
                    out.write('\n')
                    
                    # Break if perfect match is found
                    if potential_matches[i]['record linkage score'] == 1:
                        #print "Found perfect match for entity ", entity
                        perfactMatch = True


            # Close output file handle
            out.close()
            print "Completed %s dataset in %s seconds " % (dname, (time.time()-start_time) )
        
        # Close entities file handle
        entities.close()

    # Extract birth year from birth date
    def preprocessBirth(self, s):
        
        m = re.search('.*(\\d\\d\\d\\d).*',s)
        if m:
            return m.group(1)
        else:
            return 0
        
    # Match names using specified technique
    def matchNames(self, s1, s2, technique, threshold):
        if technique == "hj": # Hybrid Jaccard
            return self.matchNames_hj(s1, s2, threshold)
        else:
            return {"match":False}

    # Match names using hybrid jaccard, default threshold = 0.67
    def matchNames_hj(self,s1,s2, threshold=0.67):

        sys.path.append(os.path.join(self.absdir,'..','HybridJaccard'))
        from hybridJaccard import HybridJaccard
        match = {'match':False}
        sm = HybridJaccard(config_path=os.path.join('..',"hj_config.txt"))

        # Pre process strings
        s1 = unidecode(unicode(s1.encode('utf-8'),'utf-8')).strip().lower()
        s2 = unidecode(unicode(s2.encode('utf-8'),'utf-8')).strip().lower()

        # Keep only alpha numerics
        s1 = re.sub('[^A-Za-z0-9 ]+', ' ', s1)
        s2 = re.sub('[^A-Za-z0-9 ]+', ' ', s2)

        match['score'] = sm.sim_measure(s1.split(), s2.split())
        
        if match['score'] > threshold:
            match['match'] = True
        
        return match

def main():
    # Create record linkage instance with base database as ulan.json
    parser = OptionParser()
    parser.add_option("-d", "--data_set", dest="data_set", type="string",
                      help="Data sets")
    parser.add_option("-o", "--output_folder", dest="output_folder", type="string",
                      help="Output folder containing result")

    (options, args) = parser.parse_args()
    data_set = options.data_set
    output_folder = options.output_folder

    if output_folder is None:
        output_folder = 'questions'

    start_time = time.time()
    
    rl = recordLinkage('ulan')
    rl.findPotentialMatches(data_set, output_folder)
    
    print("--- %s seconds ---" % (time.time() - start_time))
        
if __name__ == "__main__":
    main()