# Museum Records Linkage

1. Setup Virtual Environment for python 2.7.X.

  ```
  pip install virtualenv
  virtualenv <env name>

  Unix/Mac OS : 
  source <env name>/bin/activate

  Windows:
  <env name>\scripts\activate
  ```
2. Install dependent python packages using following command
  ```
  sudo apt-get install python-dev
  pip install -r packages.txt
  ```

3. Install MongoDb and run the mongo server. (Ref: https://docs.mongodb.org/manual/installation/)
  ```
  mongod --dbpath <path to data directory>
  ```

4. Unzip 'ULAN.json.zip' and 'additional_datasets.zip' into folder '/datasets'  
 
5. Initialize mongo db using following command
  ```
  python mongo_init.py
  ```
  
6. Run record linkage between any two datasets
  ```
  Set class variables DATASET1 and DATASET2
  python RecordLink.py
  ```
