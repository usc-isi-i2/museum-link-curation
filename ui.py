from config import *
from dbMgr import *

@app.route('/test')
def default():
    return render_template('login.html')
    
@app.route('/curation')
@app.route('/v1/curation')
def show_curation():
    if current_user.is_authenticated:
        return render_template('curation.html')        
    else:
        return redirect(url_for('index'))

@app.route('/header')
def header():
    if current_user.is_authenticated:
        return render_template('header_search.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/cards')
def cards():
    if current_user.is_authenticated:
        return render_template('cards.html')
    else:
        return redirect(url_for('index'))
        
@app.route('/spec')
@app.route('/v1/spec')
def show_specs():
    return render_template('spec.html',server=server[7:-1])

@app.route('/profile')
def show_user_profile():
    if current_user.is_authenticated:
        return render_template('profile.html',museums=museums,server=server[:-1])
    return redirect('/login')
        
@app.route('/stats')
def redirectStats():
    if current_user.is_authenticated:
        return redirect(url_for("stats"))
    else:
        return redirect(url_for('index'))
        
@app.route('/results')
def show_results_page():
    if current_user.is_authenticated:
        return render_template('results.html',server=server[:-1],museums=museums.keys(),data=returnCurationResults())
    return redirect('/login')
        
@app.route('/about')
def about():
    return render_template('about.html')