# Museum Link Verification

1. Setup Virtual Environment for python 2.7.X.

  ```
  pip install virtualenv
  virtualenv <env name> --no-site-packages

  Unix/Mac OS : 
  source <env name>/bin/activate

  Windows:
  <env name>\scripts\activate
  ```
2. Install dependent python packages using following command
  ```
  pip install -r packages.txt
  ```
  (Refer to http://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py if there are any failures related to cryptography package)
  You might have to run following command
  ```
  sudo apt-get install build-essential libssl-dev libffi-dev python-dev
  ```

3. Install MongoDb and run the mongo server. (Ref: https://docs.mongodb.org/manual/installation/)
  ```
  mongod --dbpath <any directory path that mongoDb should use to store data>
  ```
  
4. Run the application using following command
  ```
  python app.py
  ```
