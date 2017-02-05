'''
Linking records of various aac affiliated museums against ULAN museum.
Record blocking using birth year and record linkage string comparison algorithms
'''

import sys, os, re, json, time
from unidecode import unidecode
from pprint import pprint
import pkg_resources

class recordLinkage:

    basedatabase = "ulan"
    basedir = 'dataset'
    topN = 3
    absdir = os.path.dirname(os.path.realpath(__file__))
    
    def __init__(self,base):
        self.basedatabase = base
    
    # Run record linkage against base database with blocking on birth year
    def findPotentialMatches(self, d):
        
        if d:
            datasets = [d]
        else:
            # Create list of all datasets available
            datasets = [dname[:dname.index('.')] for dname in os.listdir(self.basedir)]
        
        if not os.path.exists('questions'):
            os.makedirs('questions')
        
        # Iterate over all datasets
        for dname in datasets:
            
            # Skip ulan 
            if dname == self.basedatabase:
                continue

            start_time = time.time()
                
            # Open output file
            out = open(os.path.join(self.absdir,"questions",dname+".json"),'w')
                
            # Open dataset file and ulan file 
            entities = open(os.path.join(self.absdir,self.basedir,dname+".json"))
            
            # Record blocking + Record Linkage
            for entity in entities:
                # convert line read into json
                entity = json.loads(entity)
                potential_matches = []
                
                ulanentities = open(os.path.join(self.absdir,self.basedir,self.basedatabase+".json"))
                for ulanentity in ulanentities:
                    # convert line read into json
                    ulanentity = json.loads(ulanentity)
                    
                    # Check if ulan entity birth year belong to any of the block keys.
                    if self.preprocessBirth(ulanentity['byear']['value']) == self.preprocessBirth(entity['byear']['value']):
                        
                        # do string similarity
                        match = self.matchNames(ulanentity['name']['value'], entity['name']['value'],'hj')
                        
                        if match['match']:
                            potential_matches.append({"uri1":entity['uri']['value'],"uri2":ulanentity['uri']['value'],"similarity":match})
                    else:
                        continue # no match
                 
                # Close ULAN entities file handle
                ulanentities.close()
                
                # Sort potential matches based on matching score and select top N
                potential_matches = sorted( potential_matches ,key=lambda x: x['similarity']['score'],reverse=True )
                
                for i in range(0,self.topN):
                    
                    # Break if no potential matches 
                    if len(potential_matches) == 0:
                        print "No matches were found for entity", entity
                        break
                        
                    # Break if not enough potential matches 
                    elif len(potential_matches)-1 < i:
                        print "Enough matches were not found for entity", entity
                        break
                        
                    out.write(json.dumps(potential_matches[i]))
                    out.write('\n')
                    
                    # Break if perfect match is found
                    if potential_matches[i]['similarity']['score'] == 1:
                        print "Found perfect match for entity ", entity
                        break

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
    def matchNames(self, s1, s2, technique):
        if technique == "hj": # Hybrid Jaccard
            return self.matchNames_hj(s1, s2)
        elif technique == "sw": # Smith Waterman
            return self.matchNames_sw(s1, s2)
        else:
            return {"match":False}

    # Match names using hybrid jaccard
    def matchNames_hj(self,s1,s2):

        sys.path.append(os.path.join(self.absdir,'..','HybridJaccard'))
        from hybridJaccard import HybridJaccard
        
        threshold = 0.4
        match = {'match':False}
        
        sm = HybridJaccard(config_path=os.path.join('..',"hj_config.txt"))

        # Pre process strings
        s1 = unidecode(s1).strip().lower()
        s2 = unidecode(s2).strip().lower()

        # Keep only alpha numerics
        s1 = re.sub('[^A-Za-z0-9 ]+', '', s1)
        s2 = re.sub('[^A-Za-z0-9 ]+', '', s2)

        match['score'] = sm.sim_measure(s1.split(), s2.split())
        
        if match['score'] > threshold:
            match['match'] = True
        
        return match
          
    # Match names using hybrid jaccard
    def matchNames_sw(self,s1,s2):
   
        import swalign # Smith Waterman
   
        threshold = 66 # 2*match >= mismatch 
        sw_match = 2
        sw_mismatch = -1
        match = {'match':False}
        
        # do some pre processing to do fair comparison
        s1 = unidecode(s1).strip().lower().replace(" ","")
        s2 = unidecode(s2).strip().lower().replace(" ","")
        
        scoring = swalign.NucleotideScoringMatrix(sw_match, sw_mismatch)
        sw = swalign.LocalAlignment(scoring,gap_penalty=-0.5) 
        alignment = sw.align(s1,s2) 
        #alignment.dump()
        
        match['score'] = alignment.score
        match['matchC'] = alignment.matches
        match['matchP'] = alignment.identity * 100
        match['mismatches'] = alignment.mismatches

        match['tool'] = 'swalign'
        match['version'] = pkg_resources.get_distribution('swalign').version
        
        # Check word count weighted score 
        words = s1.split()
        words.extend(s2.split())
        avgwordlen = 0
        for word in words:
            avgwordlen += len(word)
                        
        avgwordlen = round(avgwordlen/float(len(words)))
                        
        if match['matchP'] > threshold and match['matchC'] >= avgwordlen:
            match['match'] = True
       
        return match

def main():
    # Create record linkage instance with base database as ulan.json
    start_time = time.time()
    
    rl = recordLinkage('ulan')
    if len(sys.argv) >= 2:
        rl.findPotentialMatches(sys.argv[1])
    else:
        rl.findPotentialMatches(None)
    
    print("--- %s seconds ---" % (time.time() - start_time))
        
if __name__ == "__main__":
    main()