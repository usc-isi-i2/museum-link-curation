import os, json

outf1 = open(os.path.join('questions','SAAMmin.json'),'w')
outf2 = open(os.path.join('entities','SAAMmin.json'),'w')
outf3 = open(os.path.join('entities','ULANmin.json'),'w')

in1 = open(os.path.join('questions','SAAM.json'))
in2 = open(os.path.join('entities','SAAM.json'))
in3 = open(os.path.join('entities','ULAN.json'))

data2 = json.loads(in2.read())["people"]
data3 = json.loads(in3.read())["people"]

json_data = in1.read()
data = json.loads(json_data)
data = data["payload"]

out1 = []
out2 = []
out3 = []

for i in range(0,100):
    out1.append(data[i])
    uri1 = data[i]["uri1"]
    uri2 = data[i]["uri2"]
    
    print (i)
    
    if "/ulan/" in uri1:
        for entity in data2:
            if entity['@id'] == uri2:
                out2.append(entity)
        for entity in data3:
            if entity['@id'] == uri1:
                out3.append(entity)
    else:
        for entity in data2:
            if entity['@id'] == uri1:
                out2.append(entity)
        for entity in data3:
            if entity['@id'] == uri2:
                out3.append(entity)

x = json.dumps({"count":100,"payload":out1},indent=4)
outf1.writelines(x)

x = json.dumps({"people":out2},indent=4)
outf2.writelines(x)

x = json.dumps({"people":out3},indent=4)
outf3.writelines(x)