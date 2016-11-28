# Identify two datasets
# Create dictionary of birth year on smaller dataset (non ulan) with value as count and key as birth year
# Basically run n^2 loop with inner loop only running when byear match

from unidecode import unidecode
from pprint import pprint
import swalign # Smith Waterman
import os, json
import pkg_resources

class recordLinkage:

    basedatabase = "ulan"
    basedir = 'dataset'
    threshold = 66 # 2*match >= mismatch 
    
    def __init__(self,base):
        self.basedatabase = base
    
    # Run record linkage against base database with blocking on byear
    def findPotentialMatches(self):
        
        datasets = [dname[:dname.index('.json')] for dname in os.listdir(self.basedir) if dname.endswith('.json')]
        
        if not os.path.exists('questions'):
            os.makedirs('questions')
        
        for dname in datasets:
            
            # Skip ulan 
            if dname == self.basedatabase:
                continue
            
            count = 0
            absdir = os.path.dirname(os.path.realpath(__file__))
            firstJsonObject = True
            
            out = open(os.path.join(absdir,"questions",dname+".json"),'w')
            out.write('{\n')
            out.write('    "payload": [\n')
                
            with open(os.path.join(absdir,self.basedir,dname+".json")) as entities:
                for entity in entities:
                    # convert line read into json
                    entity = json.loads(entity)
                    
                    # open ULAN handle - N^2 loop
                    with open(os.path.join(absdir,self.basedir,self.basedatabase+".json")) as ulanentities:
                        for ulanentity in ulanentities:
                            # convert line read into json
                            ulanentity = json.loads(ulanentity)
                            
                            # Check if ulan entity birth year belong to any of the block keys.
                            if ulanentity['byear']['value'] == entity['byear']['value']:
                                
                                # do string similarity
                                match = self.matchNames(ulanentity['name']['value'], entity['name']['value'])
                                
                                words = ulanentity['name']['value'].split()
                                words.extend(entity['name']['value'].split())
                                avgwordlen = 0
                                for word in words:
                                    avgwordlen += len(word)
                                
                                avgwordlen = round(avgwordlen/float(len(words)))
                                
                                if match['matchP'] > self.threshold and match['matchC'] >= avgwordlen:
                                    d = {"uri1":ulanentity['uri']['value'],"uri2":entity['uri']['value'],"linkage":match}
                                    count += 1
                                    
                                    # Making sure the file is valid json 
                                    if firstJsonObject:
                                        firstJsonObject = False
                                    else:
                                        out.write(',\n')
                                    out.write(json.dumps(d,indent=4))

                            else:
                                continue # no match

            out.write('    ],\n')
            out.write('    "count": {}\n'.format(count))
            out.write('    },\n')
            out.close()

    def matchNames(self,name1,name2):

        linking = {}
        
        # do some pre processing to do fair comparison
        name1 = unidecode(name1)
        name2 = unidecode(name2)
        name1 = name1.strip()
        name2 = name2.strip()
        name1 = name1.lower()
        name2 = name2.lower()
        name1 = name1.replace(" ","")
        name2 = name2.replace(" ","")
        
        match = 2
        mismatch = -1
        scoring = swalign.NucleotideScoringMatrix(match, mismatch)
        sw = swalign.LocalAlignment(scoring,gap_penalty=-0.5) 
        alignment = sw.align(name1,name2) 
        #alignment.dump()
        
        linking['score'] = alignment.score
        linking['matchC'] = alignment.matches
        linking['matchP'] = alignment.identity * 100
        linking['mismatches'] = alignment.mismatches
        linking['score'] = alignment.score

        linking['tool'] = 'swalign'
        linking['version'] = pkg_resources.get_distribution('swalign').version
        
        return linking

def main():
    # Create record linkage instance with base database as ulan.json
    rl = recordLinkage('ulan')
    rl.findPotentialMatches()
        
if __name__ == "__main__":
    main()