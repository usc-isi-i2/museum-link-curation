'''
Calcualtes Precision and recall values for linkage generated by HybridJaccard
Takes an input json file and gives output json

Input
{"similarity": {"score": 0.7042857142857143, "match": true}, "uri2": "http://vocab.getty.edu/ulan/500108546", "uri1": "http://data.americanartcollaborative.org/acm/artistobject/2357"}
{"similarity": {"score": 0.6869047619047619, "match": true}, "uri2": "http://vocab.getty.edu/ulan/500356472", "uri1": "http://data.americanartcollaborative.org/acm/artistobject/2357"}


Output
{"precision": 0.89, "recall": 0.81}	


Cases
   result             	Musuem Linkage
1) A -- B 				A -- B 				True Positive += 1
2) A -- B 				A -- C 				False Positive += 1
3) A -- B               None                True Negative += 1
4) None                 A -- B              False Negative += 1

Precison = TP / (TP + FP)
Recall = TP / (TP + FN)

'''

from SPARQLWrapper import SPARQLWrapper, JSON
import json, sys,os
import museum_graph_api_config as config
SPARQL_ENDPOINT = "http://data.americanartcollaborative.org/sparql"
from collections import defaultdict

def calculate_relevance(ipfile, museum):

	parent_uri_set = set()
	success_uri = set()
	tn = set()
	failure_uri = {}
	total_uri_set = set()
	sparql = SPARQLWrapper(SPARQL_ENDPOINT)
	sparql.setReturnFormat(JSON)
	museum_dict = {'GM': 'GM', 'IMA': 'ima'}

	data_dict = defaultdict(list)
	query = ''

	#Calculate the ground truth
	#Cacluate total URI matches for the MUSUEM
	count_query = ''
	fp = os.path.join(os.path.dirname(os.path.realpath(__file__)),'get_uri_matches.sparql')
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

	# get_ulan_uri.sparql has sparql query to fetch ULAN ID for Actor URI
	fp = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'get_ulan_uri.sparql')
	with open(fp, 'r') as query_file:
		query = query_file.read()

	with open(ipfile, 'r') as ip:
		for line in ip:
			data = json.loads(line)
			parent_uri = data["uri1"]
			ulan_uri = data["uri2"]
			similarity_score = float(data["similarity"]["score"])

			k = {'ulan_uri': ulan_uri, 'similarity': similarity_score}
			if 'ulan_name' in data:
				k['ulan_name'] = data['ulan_name']
			if 'museum_name' in data:
				k['museum_name'] = data['museum_name']

			data_dict[parent_uri].append(k)


			if parent_uri in ground_truth:
				for v in data_dict[parent_uri]:
					v['correct_ulan_uri'] = ground_truth[parent_uri]
				total_uri_set.add(parent_uri)
				if ground_truth[parent_uri] == ulan_uri:
					success_uri.add(parent_uri)
			else:
				tn.add(parent_uri)


			'''
			data_dict[parent_uri].append({'ulan_uri': ulan_uri, 'similarity': similarity_score})
			squery = query.replace('PARENT_URI', parent_uri)
			sparql.setQuery(squery)
			output = sparql.query().convert()
			#print(parent_uri, output)
			if len(output['results']['bindings']) > 0:
				total_uri_set.add(parent_uri)
				bindings = set()
				for binding in output['results']['bindings']:
					bindings.add(binding['lod_identifier']['value'])
					for v in data_dict[parent_uri]:
						v['correct_ulan_uri'] = binding['lod_identifier']['value']

				if ulan_uri in bindings:
					success_uri.add(parent_uri)
			else:
				tn.add(parent_uri)
			'''
	precision = 0
	recall = 0
	if len(total_uri_set) > 0:
		precision = float(len(success_uri)) / (len(total_uri_set))
		recall = float(len(success_uri)) / total_match_count

	failures = list(total_uri_set - success_uri)
	false_positives = defaultdict(list)
	for f in failures:
		false_positives[f] = data_dict[f]
	true_negatives = defaultdict(list)
	for f in tn:
		true_negatives[f] = data_dict[f]

	false_negatives = list(set(ground_truth.keys()) - set(data_dict.keys()))
	f_score = 0
	if (precision + recall) > 0:
		f_score = (2 * precision * recall) / (precision + recall)
	result = {'false_positives': false_positives , 'false_negatives': false_negatives, 'true_negatives': true_negatives,
				'total': [len(total_uri_set),len(data_dict.keys()), total_match_count], 'success': len(success_uri), 'precision': precision, 'recall': recall,
				'f_score': f_score}
	print(json.dumps(result))


if __name__ == '__main__':
	#print(len(sys.argv))
	#assert(len(sys.argv) != 3), "Expects a json file as argument"
	calculate_relevance(sys.argv[1], sys.argv[2])