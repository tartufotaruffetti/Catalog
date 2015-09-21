




from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import bleach
from flask.ext.seasurf import SeaSurf

app = Flask(__name__)

# SeaSurf is a Flask extention to prevent cross-site request forgeries (CSRF)
csrf = SeaSurf(app)
csrf.init_app(app)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog System App"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalogitem1.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('/login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)

    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<center><h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px;
    height: 300px;border-radius: 150px;-webkit-border-radius:
    150px;-moz-border-radius: 150px;"> '''
    output += '</center>'
    flash("you are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions
def createUser(login_session):
    '''
        creates a user in the DDBB
        Args:
        login_session: from the session we get the username, email
        and picture.
    '''
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# User Helper Functions
def getUserInfo(user_id):
    '''
        get the user data from DDBB
        Args:
            user_id: int the user id to look for in the DDBB
    '''
    user = session.query(User).filter_by(id=user_id).one()
    return user


# User Helper Functions
def getUserID(email):
    '''
        return the user id
        Args:
            email : given the email we find the user
    '''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog.JSON')
def catalogJSON():
    '''
        return a json file of the catalog; categories and items in DDBB
    '''
    list = []
    categories = session.query(Category).all()
    for category in categories:

        items = session.query(CategoryItem).filter_by(
            category_id=category.id).all()
        items_list = []
        for item in items:
            items_list.append(
                {
                    "title": item.title,
                    "item_id": item.id,
                    "description": item.description,
                    "created by": item.user.name
                }
            )
        list.append({"category": category.name,
                     "category_id": category.id,
                     "items": items_list})
    return jsonify({"catalog": list})


@app.route('/category/JSON')
def categoryJSON():
    '''
        return a json file of all categories in catalog in DDBB
    '''
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def categoryItemJSON(category_id, item_id):
    '''
        return a json file of the item in the given category
        Args:
            category_id: int the category we search for
            item:_id: int the item id we search for
    '''
    Category_Item = session.query(CategoryItem).filter_by(id=item_id).one()
    return jsonify(Category_Item=Category_Item.serialize)


@app.route('/catalog.xml/')
def catalogXML():
    '''
        return an XML file of the catalog in DDBB
    '''
    list = []
    categories = session.query(Category).all()
    list.append('<?xml version="1.0" encoding="UTF-8"?>')

    list.append('<catalog>')
    for category in categories:
        list.append
        (
            '<category name = "' + category.name +
            '" category_id = "' + str(category.id) + '" >'

        )
        items = session.query(CategoryItem).filter_by(
            category_id=category.id).all()
        for item in items:
            list.append(
                '<item ><title>' + item.title +
                '</title><id>' + str(item.id) + '</id><description>' +
                item.description + '</description><created_by>' +
                item.user.name + '</created_by></item>'
            )
        list.append('</category>')
    list.append('</catalog>')
    return str.join('\n', list), 200, {'Content-Type': 'text/xml'}


# Show all categories
@app.route('/')
@app.route('/categories/')
def showCategories():
    '''
        Return all categories in the catalog
    '''
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories)
    else:
        return render_template('categories.html', categories=categories)


# create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    '''
        Creates a new category. User must be login
        Args:
            name: a string for the category name.
                comes in the post form
    '''
    # check if user is login
    if 'username' not in login_session:
        return redirect('/login')
    # if post then we are creating
    if request.method == 'POST':
        # cleaning the variables to avoid sql injection attack
        name = bleach.clean(request.form['name'])
        name = bleach.linkify(request.form['name'])


        # validating the request form
        if not name:
            flash("Please enter a Category name.")
            return render_template('newcategory.html')


        # check if exist another category with the same name
        existingCategory = session.query(Category).filter_by(name=name).first()
        if existingCategory:
            flash
            (
                "A Category with the same name already exists. " +
                "Please choose a different name"
            )
            return render_template('newcategory.html')
        # if the name is unique then we can create
        newCategory = Category(name=name, user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        # rendering all the categories page
        return redirect(url_for('showCategories'))
    else:
        # rendering the form to create a new cat
        return render_template('newcategory.html')


# edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    '''
        Edit a category.User must be login. User can only edit
        categories he/she has created
        Args:
            category_id: the id of the category edit
            name: it comes in the post form. A string for cat name
    '''


    # check if user is login
    if 'username' not in login_session:
        return redirect('/login')
    # identify the category to edit
    editedCategory = session.query(
        Category).filter_by(id=category_id).one()
    # checking user it is the owner of the category
    if editedCategory.user_id != login_session['user_id']:

        flash("You are not authorized to execute this action")
        return redirect(url_for('showCategories'))
    # if post then we are editing
    if request.method == 'POST':
        # cleaning the variables to avoid sql injection attack
        name = bleach.clean(request.form['name'])
        name = bleach.linkify(request.form['name'])
        # validating the request form
        if not name:
            flash("Please enter a Category name.")

            # rendering the category form to edit
            return render_template(
                'editcategory.html',
                category=editedCategory
            )
        # checking there is no other category with the same name
        existingCategory = session.query(Category).filter_by(name=name).first()
        if existingCategory:
            flash
            (
                "A Category with the same name already exists. " +

                "Please choose a different name"
            )
            return render_template(
                'editcategory.html',
                category=editedCategory
            )
        # if ok we can edit
        if name:
            editedCategory.name = name
            session.add(editedCategory)
            flash('Category Successfully Edited %s' % editedCategory.name)
            session.commit()
            # rendering the all categories page
            return redirect(url_for('showCategories'))
    else:
        # rendering the category form to edit
        return render_template('editcategory.html', category=editedCategory)


# delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    '''
        Delete a category.User must be login. User can only delete
        categories he/she has created
        Args:
            category_id: the id of the category to delete
    '''


    # check if user is login
    if 'username' not in login_session:
        return redirect('/login')
    # identifying the record to delete
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    # checking user it is the owner of the category
    if categoryToDelete.user_id != login_session['user_id']:

        flash("You are not authorized to execute this action")
        return redirect(url_for('showCategories'))
    # if post then we are deleting
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        # rendering all the categories page
        return redirect(url_for('showCategories', category_id=category_id))
    else:
        # rendering the confirmatin page to delete

        return render_template(
            'deletecategory.html',
            category=categoryToDelete
        )


# show all the items of a category
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showItem(category_id):
    '''
        Shows all the items beloging to a category idetified by
        category_id.
        Args:
            category_id: the id of the category that we would like
            to see its items
    '''
    # getting the obj category
    category = session.query(Category).filter_by(id=category_id).one()
    # getting the creator/user info
    creator = getUserInfo(category.user_id)
    # getting all the items under the category
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    # if user is not login
    if 'username' not in login_session \
            or creator.id != login_session['user_id']:


        # we render just the list of items with
        # out edit delete links
        return render_template(
            'publicitem.html',
            items=items,
            category=category,
            creator=creator
        )
    else:
        # we render the list of items with edit delete links
        return render_template(
            'item.html', items=items,
            category=category, creator=creator
        )


# render the image of an item
@app.route('/item/<int:item_id>/image')
def item_image(item_id):
    '''
        render the image of an item
        Args:
            item_id: int the id of the item we wanna see the image
    '''
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    return app.response_class(
        item.image_data,
        mimetype='application/octet-stream'
    )


# create a new item in a category
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newCategoryItem(category_id):
    '''
        function to create a new item category
        Args:
            category_id: int the id of the category where we want to create
            a new item.
            We pick from the form POST the title and the description
            as well as the picture
    '''


    # make sure the user is login
    if 'username' not in login_session:
        return redirect('/login')
    # we get the category
    category = session.query(Category).filter_by(id=category_id).one()
    # make sure the user is the creator of the category
    if login_session['user_id'] != category.user_id:

        flash("You are not authorized to execute this action")
        return redirect(url_for('showCategories'))
    # if it is POST we will create
    if request.method == 'POST':
        # get the title and clean it a bit
        title = request.form['title']
        title = bleach.clean(title)
        title = bleach.linkify(title)
        # get the description and clean it a bit
        description = request.form['description']
        description = bleach.clean(description)
        description = bleach.linkify(description)


        # validating the request form
        if not title:
            flash("Please enter a Item title.")
            return render_template('newitem.html', category_id=category_id)


        newItem = CategoryItem(
            title=title,
            description=description,
            category_id=category_id,
            user_id=category.user_id

        )

        # first we are gonna declare the picture(file name)
        # and the picture data binary as none
        # validate the data and load them if necesary
        picture_data = None
        picture = None

        # verify that we are getting an image file
        # and that it is not too big>5Mb
        picture = request.files['image']
        if picture:
            # only these options are allowed as a image
            extensions = {".jpg", ".png", ".jpeg"}
            # if not we let the client know
            if not any(
                str(picture.filename).endswith(ext)

                for ext in extensions
            ):
                flash
                (
                    "Please load a Item image; " +
                    "only jpg, jpeg or png are allowed."
                )
                return render_template('newitem.html', category_id=category_id)
            else:
                # verify the size of the image
                picture_data = request.files['image'].read()
                if len(picture_data) > 5242880:
                    flash("Please load a Item image with size less than 5Mb.")

                    return render_template(
                        'newitem.html',
                        category_id=category_id
                    )
                else:
                    newItem.image = picture.filename
                    newItem.image_data = picture_data


        # verify that within the category there isn't another
        # item with the same title
        existingItem = session.query(CategoryItem).filter_by(
                    title=request.form['title'],
                    category_id=category_id).first()
        if existingItem:
            flash
            (
                "A Item with the same name already exists in this Category. " +
                "Please choose a different name"
            )
            return render_template('newitem.html', category_id=category_id)
        else:
            # create item
            session.add(newItem)
            session.commit()
            flash('New Item %s Successfully Created' % (newItem.title))
            return redirect(url_for('showItem', category_id=category_id))

    else:
        # if not login render the public page
        return render_template('newitem.html', category_id=category_id)


# edit a new item category
@app.route(
    '/category/<int:category_id>/item/<int:item_id>/edit/',
    methods=['GET', 'POST']
    )
def editCategoryItem(category_id, item_id):
    '''
        function to edit an item category
        Args:
            category_id: int category`id that item id belongs
            item_id: int the item id
            We pick from the form POST the title and the description
            as well as the picture
    '''



    # check user is login
    if 'username' not in login_session:
        return redirect('/login')
    # instanciate category and item objs.
    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    # check user is creator of the category
    if login_session['user_id'] != category.user_id:

        flash("You are not authorized to execute this action")
        return redirect(url_for('showCategories'))
    # if it is a post we are editing
    if request.method == 'POST':
        # get the title and clean it a bit
        title = request.form['title']
        title = bleach.clean(title)
        title = bleach.linkify(title)


        # get the description and clean it a bit
        description = request.form['description']
        description = bleach.clean(description)
        description = bleach.linkify(description)


        # validating the title field
        if not title:
            flash("Please enter a Item title.")
            return render_template('newitem.html', category_id=category_id)
        else:
            editedItem.title = title
        # validating the description field
        if description:
            editedItem.description = description


        # first we are gonna declare the picture(file name)
        # and the picture data (binary) as none
        # validate the data and load them if necesary
        picture_data = None
        picture = request.files['image']


        # verify that we are getting an image
        # file and that it is not too big>5Mb
        if picture:
            # only these options are allowed as a image
            extensions = {".jpg", ".png", ".jpeg"}
            # if not we let the client know
            if not any(
                str(picture.filename).endswith(ext)


                for ext in extensions
            ):
                flash
                (
                    "Please load a Item image; " +
                    "only jpg, jpeg or png are allowed."
                )
                return render_template(
                    'edititem.html',
                    category_id=category_id,
                    item_id=item_id,
                    item=editedItem
                )
            else:
                # verify the size of the image
                picture_data = request.files['image'].read()
                if len(picture_data) > 5242880:
                    flash("Please load a Item image with size less than 5Mb.")
                    return render_template(
                            'newitem.html', category_id=category_id)
                else:
                    editedItem.image = picture.filename
                    editedItem.image_data = picture_data




        # verify that within the category there isn't another
        # item with the same title
        existingItem = session.query(CategoryItem).filter_by(
                title=title, category_id=category_id).all()
        for i in existingItem:
            print("Item con ID %s", i.id)
            if i.id != editedItem.id:


                flash
                (
                    "A Item with the same name already exists in " +
                    "this Category. " +
                    "Please choose a different name"
                )
                return render_template('edititem.html',
                                       category_id=category_id,
                                       item_id=item_id,
                                       item=editedItem)
        else:
            # edit item
            session.add(editedItem)
            session.commit()
            flash('Category Item Successfully Edited')
            return redirect(url_for('showItem', category_id=category_id))
    else:
        # if not login render the public page

        return render_template(
            'edititem.html',
            category_id=category_id,
            item_id=item_id, item=editedItem
        )


@app.route('/category/<int:category_id>/item/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteCategoryItem(category_id, item_id):
    '''
        function to delete an item
        Args:
            category_id: int the category`id the item belogs to.
            item_id: int the item id to delete
    '''



    # check if user is login
    if 'username' not in login_session:
        return redirect('/login')
    # instanciate category object
    category = session.query(Category).filter_by(id=category_id).one()
    # check if user is the creator of the category
    if login_session['user_id'] != category.user_id:

        flash("You are not authorized to execute this action")
        return redirect(url_for('showCategories'))
    # instanciate items object
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    # if it is a post we are deleting
    if request.method == 'POST':
        # delete the object
        session.delete(itemToDelete)
        session.commit()
        flash('Category Item Successfully Deleted')
        return redirect(url_for('showItem', category_id=category_id))
    else:
        # render public page
        return render_template('deleteitem.html',
                               item=itemToDelete, category_id=category_id)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    '''
        to disconnect from the page
    '''
    # check that the provider is in the session
    if 'provider' in login_session:
        # if it is google+
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        # general to all providers
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        # client is not login
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


# main method
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
