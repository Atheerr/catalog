from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import User, Base, Technology, TechnologyItem
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import GoogleCredentials
import random
import string
import httplib2
import requests
import json
app = Flask(__name__)

# CLIENT_ID for Google Signin
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemShelf"

# Database session setup
engine = create_engine('postgresql://catalog:atheer@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase+string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST', 'GET'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State Parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade auth code'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # is access_token valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    # store the result of request
    result = json.loads(h.request(url, 'GET')[1])
    # if result contains any errors the message is sent to server
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # verify if this the right access_token
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Users ids do not match'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # is this token was issued for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps('Token id does not match app id'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # checks is the user already logged in not to reset all info
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data.get('name', '')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'
    user_id = getUserID(data['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '</h1>'
    return output


@app.route('/gdisconnect/')
def gdisconnect():
    access_token = login_session.get('access_token')
    print access_token
    if access_token is None:
        response = make_response(json.dumps('User is not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['user_id']
        del login_session['email']
        response = make_response(json.dumps("You are disconnected"), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/technologys')
    else:
        response = make_response(json.dumps("Error occured"), 400)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/technologys')


# User related functions for local permission system

def createUser(login_session):
    """
    createUser(login_session): creates a user
                               with given credentials
    Args:
        login_session(data-type: session) has info about
                                          the current logged user
    Returns:
        user id from database
    """
    user = User(name=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
    session.add(user)
    session.commit()
    user_db = session.query(User).filter_by(email=login_session['email']).one()
    return user_db.id


def getUserInfo(user_id):
    """
    getUserInfo(user_id): searches user-info by his id
    Args:
        user_id(data-type: int) a unique value
        that identifies a user in DB
    Returns:
        user info (username, email, picture)
    """
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def getUserID(email):
    """
    getUserID(email): searches a user by his email
    Args:
        email(data-type: string) a unique value
        that identifies a user in DB
    Returns:
        user.id or None if no such email in DB
    """
    # try:
    user = session.query(User).filter_by(email=email).one()
    return user.id
    # except:
    #     return None


@app.route('/')
@app.route('/technologys/')
def showTechnologys():
    """
    showTechnologys(): shows a list of technologys
    Args:
        None
    Returns:
        renders a template with a list of technologys
    """
    technologys = session.query(Technology).all()
    if 'username' not in login_session:
        return render_template('public_technologys.html',
                               technologys=technologys)
    else:
        return render_template('technologys.html',
                               technologys=technologys,
                               user=login_session['email'],
                               picture=login_session['picture'])


@app.route('/technologys/<int:technology_id>/')
@app.route('/technologys/<int:technology_id>/items/')
def showItems(technology_id):
    """
    showItems(): shows a list of items of a specific technology
    Args:
        technology_id (data-type: int) primary key of Technology class
    Returns:
        renders a template with a list of items of the technology
    """
    technology = session.query(Technology) \
                        .filter_by(id=technology_id).one_or_none()
    if technology is None:
        return "No such element"
    items = session.query(TechnologyItem) \
                   .filter_by(technology_id=technology_id).all()
    if 'username' not in login_session:
        return render_template('public_items.html',
                               technology=technology, items=items)
    return render_template('items.html', items=items,
                           technology=technology, user=login_session['email'])


@app.route('/technologys/new/', methods=['GET', 'POST'])
def newTechnology():
    """
    newTechnology(): creates a Technology
    Args:
        None
    Returns:
        redirects to the method that shows the
        list of technologys
    """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newTechnology = Technology(name=request.form['name'],
                                   description=request.form['description'],
                                   user_id=login_session['user_id'])
        session.add(newTechnology)
        session.commit()
        flash('Technology was successfully added to the catalog')
        return redirect(url_for('showTechnologys'))
    else:
        return render_template('newTechnology.html')


@app.route('/technologys/<int:technology_id>/items/new/',
           methods=['GET', 'POST'])
def newItem(technology_id):
    """
    newItem(technology_id): adds a TechnologyItem to Technology
    Args:
        technology_id (data type: int): primary key of Technology class
    Returns:
        redirects to the method that shows the
        list of items of technology if successful
    """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if 'type' not in request.form:
            type = 'COMPUTING'
        else:
            type = request.form['type']
        newItem = TechnologyItem(name=request.form['name'],
                                 description=request.form['description'],
                                 price=request.form['price'],
                                 user_id=login_session['user_id'],
                                 technology_id=technology_id)
        session.add(newItem)
        session.commit()
        flash('Item was successfully added to the list')
        return redirect(url_for('showItems', technology_id=technology_id))
    else:
        return render_template('newItem.html', technology_id=technology_id)


@app.route('/technologys/<int:technology_id>/edit/', methods=['GET', 'POST'])
def editTechnology(technology_id):
    """
    editTechnology(technology_id): edits a technology
    Args:
        technology_id (data type: int): primary key of Technology class
    Returns:
        redirects to the method that shows the
        list of technologys if successful
    """
    if 'username' not in login_session:
        return redirect('/login')
    technologyToEdit = session.query(Technology) \
                              .filter_by(id=technology_id).one_or_none()
    if technologyToEdit is None:
        return ("<script>function myFunction() {alert('No such element');"
                "window.history.back();}</script>"
                "<body onload='myFunction()''>")
    if technologyToEdit.user_id != login_session['user_id']:
        return ("<script>function myFunction() {alert('No access');"
                "window.history.back();}</script>"
                "<body onload='myFunction()''>")
    if request.method == 'POST':
        if request.form['name']:
            technologyToEdit.name = request.form['name']
        if request.form['description']:
            technologyToEdit.description = request.form['description']
        session.add(technologyToEdit)
        session.commit()
        flash('Technology %s was successfully edited' % technologyToEdit.name)
        return redirect(url_for('showTechnologys'))
    else:
        return render_template('editTechnology.html',
                               technology=technologyToEdit)


@app.route('/technologys/<int:technology_id>/items/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(technology_id, item_id):
    """
    editItem(technology_id, item_id): edits a TechnologyItem
    Args:
        technology_id (data type: int): id of a technology item belongs to
        item_id (data type: int): primary key for a item
    Returns:
        redirects to the method that shows the list
        of items of the technology if successful
    """
    if 'username' not in login_session:
        return redirect('/login')
    itemToEdit = session.query(TechnologyItem) \
                        .filter_by(id=item_id).one_or_none()
    if itemToEdit is None:
        return ("<script>function myFunction() {alert('No such element');"
                "window.history.back();}</script>"
                "<body onload='myFunction()''>")
    if itemToEdit.user_id != login_session['user_id']:
        return ("<script>function myFunction()"
                "{alert('No access');window.history.back();}"
                "</script><body onload='myFunction()''>")
    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']
        if request.form['price']:
            itemToEdit.price = request.form['price']
        if request.form['type']:
            itemToEdit.type = request.form['type']
        itemToEdit.id = item_id
        itemToEdit.technology_id = technology_id
        session.add(itemToEdit)
        session.commit()
        flash('Item %s was successfully edited' % itemToEdit.name)
        return redirect(url_for('showItems', technology_id=technology_id))
    else:
        return render_template('editItem.html', technology_id=technology_id,
                               item_id=item_id, item=itemToEdit)


@app.route('/technologys/<int:technology_id>/delete/', methods=['GET', 'POST'])
def deleteTechnology(technology_id):
    """
    deleteTechnology(technology_id): deletes a Technology
    Args:
        technology_id (data type: int): primary key of technology
    Returns:
        redirects to the method that shows the
        list of technologys if successful
    """
    if 'username' not in login_session:
        return redirect('/login')
    technologyToDelete = session.query(Technology) \
                                .filter_by(id=technology_id).one_or_none()
    if technologyToDelete is None:
        return ("<script>function myFunction() {alert('No such element');"
                "window.history.back();}</script>"
                "<body onload='myFunction()''>")
    if technologyToDelete.user_id != login_session['user_id']:
        return ("<script>function myFunction()"
                "{alert('No access');"
                "window.history.back();"
                "}</script><body onload='myFunction()''>")
    if request.method == 'POST':
        session.delete(technologyToDelete)
        session.commit()
        flash('Technology was successfully deleted from the catalog')
        return redirect(url_for('showTechnologys',
                                technology_id=technology_id))
    else:
        return render_template('deleteTechnology.html',
                               technology=technologyToDelete)


@app.route('/technologys/<int:technology_id>/items/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(technology_id, item_id):
    """
    deleteItem(technology_id, item_id): deletes a TechnologyItem
    Args:
        technology_id (data type: int): id of a technology item belongs to
        item_id (data type: int): primary key for a item
    Returns:
        redirects to the method that shows the
        list of items of technology if successful
    """
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(TechnologyItem) \
                          .filter_by(id=item_id).one_or_none()
    if itemToDelete is None:
        return ("<script>function myFunction() {alert('No such element');"
                "window.history.back();"
                "window.history.back();}</script>"
                "<body onload='myFunction()''>")
    if itemToDelete.user_id != login_session['user_id']:
        return ("<script>function myFunction()"
                "{alert('No access');}</script><body onload='myFunction()''>")
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item was successfully deleted from the list')
        return redirect(url_for('showItems', technology_id=technology_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


# JSON API endpoints
@app.route('/technologys/JSON/')
def technologysJSON():
    technologys = session.query(Technology).all()
    return jsonify(technologys=[g.serialize for g in technologys])


@app.route('/technologys/<int:technology_id>/items/JSON/')
def showItemsJSON(technology_id):
    technology = session.query(Technology) \
                        .filter_by(id=technology_id).one_or_none()
    if technology is None:
        return "No such element."
    items = session.query(TechnologyItem) \
                   .filter_by(technology_id=technology_id).all()
    return jsonify(items=[b.serialize for b in items])


@app.route('/technologys/<int:technology_id>/items/<int:item_id>/JSON/')
def showTechnologyItemJSON(technology_id, item_id):
    Item_Item = session.query(TechnologyItem) \
                       .filter_by(id=item_id).one_or_none()
    if Item_Item is None:
        return "No such element."
    return jsonify(Item_Item=Item_Item.serialize)


if __name__ == '__main__':
    app.secret_key = 'some_very_difficult_key_to_protect_data'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
