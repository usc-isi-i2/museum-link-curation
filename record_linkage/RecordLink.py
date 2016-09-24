# Dedupe 
# Gregg, Forest, and Derek Eder. 2016. Dedupe. https://github.com/datamade/dedupe.

from __future__ import print_function
from future.builtins import next

import os, re
import glob, json, csv
import pymongo
import collections
import logging, optparse
import numpy, dedupe

class RecordLink:

    # Class variables
    PRIMARYDATASET = 'ULAN.json' 
    VERSION_NUM = 1.1 # Version
    BASE = "dedupe"
    OUTPUT_FILE = os.path.join(BASE,'recordlinks.json')
    SETTINGS_FILE = os.path.join(BASE,'data_matching_learned_settings')
    TRAINING_FILE = os.path.join(BASE,'data_match.json')
    COMPARE_FIELDS = ['schema:name', 'schema:birthDate', 'schema:deathDate'] 
    MAX_BLOCK_SQUARE = 750000 # size of block1 * block2, determines memory usage
    NUM_CORES = 4 # Used only during manual training 
    SAMPLE_SIZE = 10000 # Sample size for manual training
    THRESHOLD = 0.5 # dedupe similarity threshold 
    LETTERS = map(chr, range(ord('a'), ord('z')+1)) # Create a list containing characters from a to z

    # Create MongoDb client and database named "recordLinkage"
    # We populate two tables: artists and linkRecords
    #client = pymongo.MongoClient('localhost', 12345)
    client = pymongo.MongoClient('localhost', 27017)
    db = client["recordLinkage"]

    # Return list of datasets to be linked with ULAN
    def getDatasets(self) : 
        cursor = self.db.artists.distinct('dataset')
        datasets = list(cursor)
        
        if 'ULAN.json' in datasets:
            datasets.remove('ULAN.json')
        
        print ("Databases being linked to ULAN: "+str(datasets) )
        return datasets
    
    # Loads block of dataset with matching name_prefix
    def loadBlock(self, dataset, name_prefix):
        
        # Add all compare fields and initialize to dummy value, i.e. 1
        selected_fields = {'@id': 1}
        for field in self.COMPARE_FIELDS:
            selected_fields[field] = 1

        # Find records from dataset
        # filter them if name_prefix matches any element of nameSplit list at beginning case insensitively 
        # Return selected_fields for matched criteria 
        cursor = self.db.artists.find( {"dataset": dataset, 
                                        "nameSplit": { '$regex':'^{0}'.format(name_prefix), '$options': 'i' }},
                                        selected_fields )

        # Create dictionary with key as URI and value as non-URI field-value pairs
        data_d = {}
        for person in cursor:
            fields = {}
            #check for missing fields, make them null
            for field_name in self.COMPARE_FIELDS:
                if field_name in person:
                    # dedupe comparison requires strings
                    if str(person[field_name]) == "":
                        fields[field_name] = None
                    else:
                        fields[field_name] = unicode(person[field_name])
                else:
                    fields[field_name] = None
                    
            data_d[person['@id']] = fields
        
        # Return dictionary of all records in the selected data block
        return data_d

    # Call csv dedupe functions to do record linking
    def linkRecords(self, data_1, data_2):
        
        # Train manually if settings file not provided
        if os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, 'rb') as sf :
                ddLinker = dedupe.StaticRecordLink(sf)
        else:
            fields = [
                {'field':unicode('schema:name'), 'type':'String'},
                {'field':unicode('schema:birthDate'), 'type':'ShortString', 'has missing':True},
                {'field':unicode('schema:deathDate'), 'type':'ShortString', 'has missing':True}
            ]

            ddLinker = dedupe.RecordLink(fields, num_cores=self.NUM_CORES)
            print('created linker')
            ddLinker.sample(data_1, data_2, self.SAMPLE_SIZE)
            print('created linker sample')

            if os.path.exists(self.TRAINING_FILE):
                print('reading labeled examples from ', self.TRAINING_FILE)
                with open(self.TRAINING_FILE) as tf :
                    ddLinker.readTraining(tf)

            print('starting active labeling...')

            dedupe.consoleLabel(ddLinker)

            ddLinker.train()

            with open(self.TRAINING_FILE, 'w') as tf : #write training file
                ddLinker.writeTraining(tf)

            with open(self.SETTINGS_FILE, 'wb') as sf : #write dedupe settings file
                ddLinker.writeSettings(sf)
            
        # Run Record Blocking 
        for field in ddLinker.blocker.index_fields:
            print ('Record blocking with field -> '+field)
            # Get attributes from first block
            field_data1 = set(record[1][field] for record in data_1.items())
            # Get attributes from second block
            field_data2 = set(record[1][field] for record in data_2.items()) 
            # Union attributes from both blocks
            field_data = field_data1 | field_data1 
            
            # Run csv dedupe blocker
            # print ('Record blocking on data '+str(field_data))
            ddLinker.blocker.index(field_data, field)

        # Filter blocker blocks if left or right value is not matched
        blocks = collections.defaultdict(lambda : ([], []) )
        # Read blocker blocks from left block
        for block_key, record_id in ddLinker.blocker(data_1.items()) :
            blocks[block_key][0].append((record_id, data_1[record_id], set([])))
        # Read blocker blocks from right block
        for block_key, record_id in ddLinker.blocker(data_2.items()) :
            if block_key in blocks:
                blocks[block_key][1].append((record_id, data_2[record_id], set([])))
        # Delete blocker blocks if either left or right block is empty
        for k, v in blocks.items():
            if not v[1] or not v[0]:
                del blocks[k]

        # Match blocks with predefined threshold value 
        linked_records = ddLinker.matchBlocks(blocks.values(), threshold=self.THRESHOLD) 
        
        return linked_records

    # Write matched records in table linkRecords
    def dbOutput(self, linked_records, dataset) :
        for record in linked_records:
            # print ('Writing following record to database')
            # print (record)
            
            link = {'uri1': record[0][0], 
                    'uri2': record[0][1], 
                    'dedupe': {'version': unicode(self.VERSION_NUM), 
                               'linkscore': unicode(record[1]),
                               'fields': self.COMPARE_FIELDS, 
                               'dataset': dataset } }
            
            self.db.linkRecords.insert(link)
        
        # Dumping output to file for every iteration - Temporary Fix 
        self.output_links(linker.OUTPUT_FILE)
            
    # Core function running csv dedupe
    def getLinkedRecords(self, name_prefix, dataset):
        # Step1: Create blocks of data from both datasets
        data_1 = self.loadBlock(self.PRIMARYDATASET, name_prefix)
        data_2 = self.loadBlock(dataset, name_prefix)
        
        print ( 'Blocking for name prefix: {}'.format(name_prefix) )
        print ( '[Block1,Block2,Max]:[{},{},{}]'.format(len(data_1), len(data_2),self.MAX_BLOCK_SQUARE) )
        
        # Return if either of the blocks are empty
        if len(data_1) == 0 or len(data_2) == 0:
            return 
        
        # Step2: if block1*block2 has more block then predefined MAX
        if (len(data_1) * len(data_2)) > self.MAX_BLOCK_SQUARE:
            # recursively call this function with new name_prefix
            for letter in self.LETTERS:
                new_name_prefix = name_prefix + letter
                self.getLinkedRecords(new_name_prefix, dataset)
        
        else:
            # link records from both blocks and load them into database
            linked_records = linker.linkRecords(data_1, data_2)
            # Store matched records in linkRecords table
            self.dbOutput(linked_records, dataset)
            print('linked {} records from dataset {} on blocking {}'.format(len(linked_records),dataset,name_prefix) )

    # Output bulk pair of entities matched by csv dedupe
    def output_links(self, outputFile):
        cursor = self.db.linkRecords.find()
        records = (list(cursor))
        
        # Remove entries missing _id
        for record in records:
            record.pop('_id', None)
            
        # Format json with bulk=record count and payload=actual records 
        # This format is consistent with one used with REST API to load records 
        output = {"bulk": len(records), "payload": records}
        
        with open(outputFile, 'w') as out :
            x = json.dumps(output)
            out.writelines(x)

if __name__ == "__main__":

    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose', dest='verbose', action='count',
                        help='Increase verbosity (specify multiple times for more)')
    (opts, args) = optp.parse_args()
    log_level = logging.WARNING 
    
    if opts.verbose :
        if opts.verbose == 1:
            log_level = logging.INFO
        elif opts.verbose >= 2:
            log_level = logging.DEBUG
    logging.getLogger().setLevel(log_level)

    # Initialize RecordLink Object and drop old linkRecords table 
    linker = RecordLink()
    linker.db.linkRecords.drop()

    # Get list of datasets to be compared with ULAN
    datasets = linker.getDatasets()
    
    # Link records of every dataset with ULAN and populate linkRecords table
    for dataset in datasets: 
        for letter1 in linker.LETTERS:
            #initially block by first two letter of each name
            for letter2 in linker.LETTERS:
                linker.getLinkedRecords(letter1+letter2, dataset)

        cursor = linker.db.linkRecords.find()
        print('Total linked records: ', len(list(cursor)))

    # Write linked records (questions) to output file
    #linker.output_links(linker.OUTPUT_FILE)