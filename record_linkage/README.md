# museum_record_link

For Windows: Install VS tools from http://landinghub.visualstudio.com/visual-cpp-build-tools

pip install -r packages.txt

Unzip 'ULAN.json.zip' and 'additional_datasets.zip' into folder '/datasets'

Run mongo_init.py to load datasets into local MongoDB database

Run RecordLink.py to link records between any two datasets
  Set class variables DATASET1 and DATASET2
