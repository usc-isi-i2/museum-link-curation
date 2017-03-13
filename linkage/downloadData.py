from SPARQLWrapper import SPARQLWrapper, JSON
import os, sys, json

map = {'ulan':"http://vocab.getty.edu/sparql",
       'aac':"http://data.americanartcollaborative.org/sparql"}

files = os.listdir( os.path.join(os.path.dirname(os.path.realpath(__file__)),'sparql'))

if not os.path.exists('dataset'):
    os.makedirs('dataset')
    
# Iterate over all SPARQL files
for f in files:
    # Extract museum name
    base = f[:f.index('.')] # ulan, npg etc.
    f_in = open(os.path.join('sparql',f), 'r')
    
    # Send SPARQL query
    if base == 'ulan':
        sparql = SPARQLWrapper(map['ulan'])
    else:
        sparql = SPARQLWrapper(map['aac'])
        
    print "Downloading ",base," dataset"
        
    sparql.setQuery(f_in.read())
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    f_in.close()
                
    # Save the results
    out = open(os.path.join('dataset',base+'.json'),'w')
    for entity in results["results"]["bindings"]:
        out.write(json.dumps(entity))
        out.write("\n")
    out.close()