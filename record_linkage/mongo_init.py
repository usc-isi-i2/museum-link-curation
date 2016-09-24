#Cleans and loads datasets into local mongodb for local record linkage

from __future__ import with_statement

import os, sys, datetime, re
import glob, json, csv
import logging
import pymongo
from bson.json_util import dumps
from unidecode import unidecode

class MongoInit:

    # Create MongoDb client and database named "test"
    # We populate two tables: artists and linkRecords
    #client = pymongo.MongoClient('localhost', 12345)
    client = pymongo.MongoClient('localhost', 27017)
    db = client["recordLinkage"]
    path = 'datasets'
    current_year = datetime.datetime.now().year

    # Read datasets from "datasets" directory and load all of them into mongoDb
    def load_dataset(self):
        datasets = [dname for dname in os.listdir(self.path) if dname.endswith('.json')]
        for dname in datasets:
            f = open(os.path.join(self.path,dname))
            print("Reading dataset file "+dname)
            
            people = json.loads(f.read())["people"]
            print("Total records in dataset : {}".format(len(people)))
            
            for person in people:
                if 'schema:name' in person:
                    if 'schema:deathDate' in person:
                        person['schema:deathDate'] = self.fixDeathDate(person['schema:deathDate'])
                    if 'schema:birthDate' in person:
                        person['schema:birthDate'] = self.getYearDate(person['schema:birthDate'])
                    person['schema:name'] = unidecode(person['schema:name']) 
                    person['dataset'] = dname 
                    person['schema:familyName'] = person['schema:name'].split(' ')[-1]
                    #split name into array for blocking
                    person['nameSplit'] = person['schema:name'].split(' ') 
                    result = self.db.artists.insert(person)

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
                    
    # Reset deathDate attribute for which date year is higher than current year. 
    def fixDeathDate(self, deathDate):
        deathDate = self.getYearDate(deathDate)
        if deathDate:
            try:
                dd = int(deathDate)
                # Set deathDate to empty string when it is in future 
                if dd > self.current_year:
                    deathDate = None
            except ValueError:
                return deathDate
        return deathDate

    # Create Mongo Db indexes 
    def create_indexes(self):
        self.db.artists.create_index([("@id", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:name", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:familyName", pymongo.ASCENDING)])
        self.db.artists.create_index([("nameSplit", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:birthDate", pymongo.ASCENDING)])
        self.db.artists.create_index([("schema:deathDate", pymongo.ASCENDING)])
        self.db.artists.create_index([("dataset", pymongo.ASCENDING)])

if __name__ == "__main__":

    mongo = MongoInit()
    mongo.db.artists.drop()
    mongo.load_dataset()
    mongo.create_indexes()
    
    cursor = mongo.db.artists.find()
    print (len(list(cursor)))