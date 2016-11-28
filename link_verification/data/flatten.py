import json
infile = open('npg_master.json','r')
outfile = open('npg_master_formatted.json','w')

outfile.writelines(json.dumps(json.loads(infile.read()),indent=4))

