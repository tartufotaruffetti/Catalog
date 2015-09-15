# **Catalog System App**


##**Background**
Application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items. Correspond to the third project within the Udacity FullStack Developer Nanodegree.


##**Description**
Application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items. The homepage displays all current categories. Selecting a specific category shows you all the items available for that category. After logging in, a user has the ability to add, update, or delete item information. The application should provide a JSON and XML endpoints


###**Modules**
1. application.py :  This is the main python module that contains the implementation of the functionality. It is build with Flask Framework. 
2. database_setup.py : This is the python module that contains the database schema and once ran it creates all the tables and views need. It is build around with SQLAlchemy. It will generate a catalog.db file.
3. lotsofcategoryitems.py :  This is module to polulate database with sample data.
4. static/styles.css : CSS style for all html pages.
5. templates/categories.html : Show all categories when login.
6. templates/deletecategory.html :  page to delete a category.
7. templates/deleteitem.html :  page to delete an item.
8. templates/editcategory.html : Fpage to edit a category.
9. templates/edititem.html :  Page to delete an item.
10. templates/header.html : The header for all pages.
11. templates/item.html : Show all items with an category.
12. templates/login.html : Login page.
13. templates/main.html : main holder, it is extended by others.
14. templates/newcategory.html :  Page to add a new category.
15. templates/newitem.html : page to add a new item. 
16. templates/publiccategories.html : Show all categories when user is noy login.
17. templates/publicitem.html :  Show all items when user is not login.

##How to use it
run ``` python application.py ```

##License and Copyright
Released under the MIT License.

##Documentation
The following is just a brief description of each method within the tournament.py  module:

1. application.py : Main Flask App that controls the flow of the requests. Please for detail see the application.py module.
2. database_setup.py : set up DDBB.
3. lotsofcategoryitems.py : Fillin DDBB with sample data.


##Previous Setup
1. Go to http://console.developers.google.com
2. Once log in, create a project and name it: Catalog System App. Google authomatically creates a Project ID for you.
3. Once you created the project Google will take you to the Project Dashboard.
4. Go to the left hand Menu and clic API and auth, select credentials.
5. In the OAuth Section clic create Client ID, make sure Web Application option is checked and then clic configure consent screen. The Consent Screen is the screen that will appeard when our app tries to connect to the google account.
6. You must specify at least an email and the Product Name: catalog System App. Save the changes and then clic create client id.
7. Now that we have a Client ID and client secret, let Edit the Configuration. In out authorized JavaScript origins (Orígenes de JavaScript autorizados) add the value "http://localhost:5000". this is needed for our local version of the code to work. Then click update
8. Download the client_secret as json file and sve it next to application.py with the name client_secret.json.
9. Please update the login.html, where it says:data-clientid="CLIENT_ID" with your client_id.


##Installation
If you would like to run this project using the Udacity VM you will need to do the following: 

1. Install Git. If you don't already have Git installed, download Git from http://git-scm.com/. Install the version for your operating system.
2. Install VirtualBox. VirtualBox is the software that actually runs the VM. You can download it from https://www.virtualbox.org/ , here. Install the platform package for your operating system.  You do not need the extension pack or the SDK. You do not need to launch VirtualBox after installing it.Ubuntu 14.04 Note: If you are running Ubuntu 14.04, install VirtualBox using the Ubuntu Software Center, not the virtualbox.org web site. Due to a reported bug, installing VirtualBox from the site may uninstall other software you need.
3. Install Vagrant. Vagrant is the software that configures the VM and lets you share files between your host computer and the VM's filesystem. Install from https://www.vagrantup.com/
4. Use Git to fetch the VM configuration. Use the Git Bash program (installed with Git) or a terminal and run : ``` git clone http://github.com/udacity/fullstack-nanodegree-vm fullstack ```
5. Using the terminal, change directory to fullstack/vagrant (cd fullstack/vagrant), then type vagrant up to launch your virtual machine. 
6. type vagrant ssh to log into it. 
7. type ```cd /vagrant/catalog``` . Make sure all files from this repo are in the directory tournament , you can either copy directly or clone them from github. Check everything is in place by typing ``` ls ``` and you should see the three main files; application.py, database_setup.py and lotsofcategoryitems.py
8. run ``` python database_setup.py ``` to config the database.
9. run ``` python lotsofcategoryitems.py ```. This should populate the database.
10. run ``` python application.py ```.
11. if everything went ok, then you should see the webpage at http://localhost:8000!

##Authors
Tartufo Taruffetti
