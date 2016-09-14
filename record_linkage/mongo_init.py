#Cleans and loads datasets into local mongodb for local record linkage

from __future__ import with_statement

import os
import glob
import sys
import logging
import pymongo
import json
import csv
import datetime
from bson.json_util import dumps
from unidecode import unidecode
import re
#from RecordLink import RecordLink

class MongoInit:

    client = pymongo.MongoClient()
    db = client.test
    path = 'datasets'
    current_year = datetime.datetime.now().year

    def load_dataset(self):
        datasets = [dname for dname in os.listdir(self.path) if dname.endswith('.json')]
        for dname in datasets:
            f = open(os.path.join(self.path,dname))
            print("Reading dataset file "+dname)
            
            people = json.loads(f.read())["people"]
            for person in people:
                if 'schema:name' in person:
                    if 'schema:deathDate' in person:
                        person['schema:deathDate'] = self.fixDeathDate(person['schema:deathDate'])
                    if 'schema:birthDate' in person:
                        person['schema:birthDate'] = self.getYearDate(person['schema:birthDate'])
                    person['schema:name'] = unidecode(person['schema:name']) #change names to ASCII
                    person['dataset'] = dname #record dataset person is from
                    person['schema:familyName'] = person['schema:name'].split(' ')[-1]
                    person['nameSplit'] = person['schema:name'].split(' ') #split name into array for blocking
                    result = self.db.artists.insert(person)

    # Reset deathDate attribute for which date year is higher than current year. 
    def fixDeathDate(self, deathDate):
        deathDate = self.getYearDate(deathDate)
        if deathDate:
            try:
                dd = int(deathDate)
                if dd > self.current_year:
                    deathDate = ''
            except ValueError:
                #print(deathDate)
                return deathDate
        return deathDate

    # Extract year from dates
    def getYearDate(self, date):
        if date:
            try:
                return int(date)
            except ValueError:
                year = re.search('(\d+)-.*', date)
                if year:
                    return year.group(1)
        else:
            return date

    # Create Mongo Db indices
    def create_indexes(self):
        self.db.artists.create_index([("@id", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:name", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:familyName", pymongo.ASCENDING)])
        self.db.artists.create_index([("nameSplit", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:birthDate", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:deathDate", pymongo.ASCENDING)])
        self.db.artists.create_index([("dataset", pymongo.ASCENDING)])

    def output_links(self, outputFile):
        cursor = self.db.linkRecords.find()
        records = (list(cursor))
        print(len(records))
        for record in records:
            record.pop('_id', None)
        output = {"bulk": len(records), "payload": records}
        with open(outputFile, 'w') as out :
            x = json.dumps(output)
            out.writelines(x)

if __name__ == "__main__":

    mongo = MongoInit()
    #mongo.output_links('newoutput.json')
    mongo.db.artists.drop()
    mongo.load_dataset()
    mongo.create_indexes()
    cursor = mongo.db.artists.find()
    print (len(list(cursor)))