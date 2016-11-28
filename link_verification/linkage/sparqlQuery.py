from SPARQLWrapper import SPARQLWrapper, JSON
import os, sys, json

map = {'ulan':"http://vocab.getty.edu/sparql",
       'npg':"http://data.americanartcollaborative.org/sparql"}

files = os.listdir( os.path.dirname(os.path.realpath(__file__)) )

if not os.path.exists('dataset'):
    os.makedirs('dataset')

# This would print all the files and directories
for f in files:
    if os.path.isfile(f):
        if ".sparql" in f:
            # Check for curation spraql 
            base = f[:f.index('.sparql')] # ulan, npg etc.
            f_in = open(f, 'r')
            
            # Send sparql query
            sparql = SPARQLWrapper(map[base])
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