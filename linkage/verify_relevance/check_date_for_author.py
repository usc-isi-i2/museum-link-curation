from SPARQLWrapper import SPARQLWrapper, JSON
import json, sys, re
import museum_graph_api_config as config
SPARQL_ENDPOINT = "http://data.americanartcollaborative.org/sparql"
ULAN_SPARQL_ENDPOINT = "http://vocab.getty.edu/sparql"
from collections import defaultdict


def get_musuem_ulan_matches(musuem):
	sparql = SPARQLWrapper(SPARQL_ENDPOINT)
	sparql.setReturnFormat(JSON)
	museum_dict = {'GM': 'GM', 'IMA': 'ima', 'WAM': 'wam'}

	data_dict = defaultdict(list)
	query = ''

	#Calculate the ground truth
	#Cacluate total URI matches for the MUSUEM
	count_query = ''
	fp = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'get_uri_matches.sparql')
	with open(fp, 'r') as query_file:
		# get_ulan_uri.sparql has sparql query , need to replace PARENT_URI with actual URI
		get_query = query_file.read()
	museum_uri = museum_dict[museum]
	get_query = get_query.replace('MUSUEM_URI', museum_uri)
	sparql.setQuery(get_query)
	result = sparql.query().convert()

	ground_truth = {}
	#convert to dict {'Actor_URI': Ulan_URI}
	for v in result['results']['bindings']:
		ground_truth[v['uri']['value']] = v['lod_identifier']['value']

	#there are some duplicates so consider as a set
	total_match_count = float(len(set(ground_truth.keys())))

	return ground_truth

# Extract birth year from birth date
def preprocessBirth(s):
    
    m = re.search('.*(\\d\\d\\d\\d).*',s)
    if m:
        return m.group(1)
    else:
        return 0

def get_birth_year(URI, MUSEUM):
	result = []

	if MUSEUM == 'ULAN':
		sparql = SPARQLWrapper(ULAN_SPARQL_ENDPOINT)
		sparql.setReturnFormat(JSON)
		fp = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'get_ulan_author_birth_date.sparql')
		with open(fp, 'r') as query_file:
			query = query_file.read()
			query = query.replace('ULAN_URI', URI)

		sparql.setQuery(query)
		result = sparql.query().convert()
		#print('ULAN',result)
		val = result['results']['bindings']
		if len(val) > 0:
			return preprocessBirth(val[0]['byear']['value'])
		else:
			return "NOT FOUND"

	else:
		sparql = SPARQLWrapper(SPARQL_ENDPOINT)
		sparql.setReturnFormat(JSON)
		fp = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'author_birth_date.sparql')
		with open(fp, 'r') as query_file:
			query = query_file.read()
			query = query.replace('AUTHOR_URI', URI)

		sparql.setQuery(query)
		result = sparql.query().convert()
		#print('MUSUEM',result)
		val = result['results']['bindings']
		if len(val) > 0:
			return preprocessBirth(val[0]['byear']['value'])
		else:
			return "NOT FOUND"


def match_dates(ulan_matches):
	result = {}
	s_matches = 0
	f_matches = 0
	failures = {}
	for author_uri, ulan_uri in ulan_matches.items():
		m_byear = get_birth_year(author_uri, 'MUSEUM')
		u_byear = get_birth_year(ulan_uri, 'ULAN')
		#print(m_byear, u_byear, m_byear == u_byear)
		if m_byear == u_byear:
			s_matches += 1
		else:
			f_matches += 1
			failures[author_uri] = {'ulan': {'ulan_uri': ulan_uri, 'u_byear': u_byear}, 'm_byear': m_byear}

	return {'failures': failures, 's_matches': s_matches, 'f_matches': f_matches}


if __name__=='__main__':

	museum = sys.argv[1]
	output = get_musuem_ulan_matches(museum)
	#print(output)
	result = match_dates(output)
	print(json.dumps(result))

