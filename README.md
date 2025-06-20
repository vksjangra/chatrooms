# Chatrooms

#### Video Demo:  <URL HERE>

#### Description:

This is a chatrooms app in which the user can create or join other chatrooms and chat with other people. Though it can be easily implemented, There is no limit to the number of participants in a chatroom!

The user has to first register an account with a username that has not been taken already. The user is then taken to the page where all the currently existing chatrooms are displayed and the user can either create a new chatroom or join an already existing one.

Once the user has joined a chatroom, there is a notification sent in the room about the user joining the room.
The user can type messages and send to the room. The message is sent to all the other users who are in the room already.

This app uses sqlite3 database to keep track of the messages and timestamp. One can join any chatroom and can see the last 50 messages in the chatroom at any point of time. So if a user miss a chat, they can see the messages later whenever they want. There is also a functionality by which a user can see all the chat history from the beginning of the chat if they want to.

The creater of the chatroom can delete that room whenever they want to. Once deleted, all the chat history will be irreversibly deleted as well.


## Files:

#### requirements.txt:
This file contains the libraries/frameworks required for this application to work. A person must install these in order for the project to run.


#### README.md:
This file contains the description and details about the application.


#### app.py:
This is the heart of the project. This file contains all the backend code written using python. This contains the backend logic of handling the sqlite3 database, handling responses to the user interface, handling all the backend logic, flask, flask-socketio etc. Handling login, registeration, creating a room, handling frontend requests, handling room joining/leaving logic, handling sending chat messages, all is done in this file.


#### chatrooms.db:
This is the sqlite3 database file which contains users, chats, chatrooms tables. The chats are stored in this database so the chats doesn't go away when the users logout. Users can access the chats of a chatroom anytime they want.


#### templates/layout.html:
This is the layout for the frontend part of this project. All the other pages are built on this layout. It contains the navbar, bootstrap link, socket io link, stylesheet link etc. All the other html files extends from this file. It contains the main HTML with head, body, header and a main part where other html files extends from.


#### static/favicon.ico:
This is a message icon which is well suited for this chatapp.


#### static/styles.css:
This file contains most of the CSS which has been used to style the user interface of this project. Some styling is directly used in the HTML files.