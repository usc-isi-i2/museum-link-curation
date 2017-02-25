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
        
@app.route('/cards')
def cards():
    if current_user.is_authenticated:
        return render_template('cards.html')
    else:
        return redirect(url_for('index'))
        
@app.route('/spec')
def show_specs():
    return render_template('spec.html',server=server[7:-1])

@app.route('/profile')
def show_user_profile():
    if current_user.is_authenticated:
        keys = [t for t in sorted(museums.keys()) if t != "ulan" ]
        return render_template('profile.html',keys=keys,museums=museums,server=server[:-1])
    return redirect('/login')
                
@app.route('/results')
def show_results_page():
    if current_user.is_authenticated:
        keys = [t.upper() for t in sorted(museums.keys())]
        return render_template('results.html',keys=keys,server=server[:-1])
    return redirect('/login')
        
@app.route('/about')
def about():
    return render_template('about.html')