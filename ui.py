from config import *
from dbMgr import *

@app.before_request
def clear_trailing():
    rp = request.path 
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])

@app.route('/test')
def default():
    return render_template('login.html')
    
@app.before_request
def before():
    logging.info("IP address: {}".format(request.remote_addr))
    #logging.info("Received request with header: {}".format(request.headers))
    pass
    
@app.route('/curation')
def show_curation():
    if current_user.is_authenticated:
        return render_template('curation.html')
    else:
        return redirect(url_for('index'))
            
@app.route('/datatable')
def datatable():
    if current_user.is_authenticated:
        return render_template('datatable.html',server=server[:-1],keys=sorted(museums.keys()),data=returnCurationResults())
    else:
        return redirect(url_for('index'))
        
@app.route('/jsonlines', methods=['GET'])
def downloadJsonlines():

    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return send_from_directory(directory=rootdir, filename="results.json",as_attachment=True)
        
@app.route('/triples', methods=['GET'])
def downloadTriples():

    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return send_from_directory(directory=rootdir, filename="results.nt",as_attachment=True)
        
@app.route('/spec')
def show_specs():
    return render_template('spec.html',server=server[7:-1])

@app.route('/profile')
def show_user_profile():
    if current_user.is_authenticated:
        # Get Keys
        keys = [t for t in sorted(museums.keys()) if t != "ulan" ]
        
        # Get User stats
        # getStats about all the questions answered by this user
        u = dbC[dname]["curator"].find_one({'uid':current_user.email},projection={'_id':False})
        answers = dbC[dname]["answer"].find({'author':current_user.email})
        
        # Initialize per museum stats 
        stats = {}
        for tag in museums.keys():
            stats[tag] = {"matched":0,"unmatched":0,"no-conclusion":0}
        
        for a in answers:
            # find question and check its current status 
            q = dbC[dname]["question"].find_one({'_id':ObjectId(a['qid'])})
            
            for tag in q['tags']:
                tag = dbC[dname]["tag"].find_one({'_id':ObjectId(tag)})['tagname']
                if q['status'] == statuscodes["Agreement"]:
                    stats[tag]["matched"] += 1
                elif q['status'] == statuscodes["Disagreement"]:
                    stats[tag]["unmatched"] += 1
                elif q['status'] == statuscodes["Non-conclusive"]:
                    stats[tag]["no-conclusion"] += 1
                    
        return render_template('profile.html',keys=keys,museums=museums,userStats=stats,server=server[:-1])
    
    return redirect('/login')
                
@app.route('/results')
def show_results_page():
    if current_user.is_authenticated:
        keys = [t for t in sorted(museums.keys())]
        return render_template('results.html',keys=keys,server=server[:-1])
    return redirect('/login')

@app.route('/stats',methods=['GET'])
def get_museum_stats():
    tag = request.args['tag'].lower()
    
    #print "Received stats request for tag : "+tag
    logging.info("Received stats request for tag : {}".format(tag))
    
    if current_user.is_authenticated:
        return jsonify(museums[tag])
    return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/done')
def done():
    if current_user.is_authenticated:
        return render_template('done.html')
    return redirect('/login')
    
@app.route('/about')
def about():
    return render_template('about.html')
