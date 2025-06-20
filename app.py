from flask import Flask, flash, redirect, render_template, request, session
from flask_socketio import send, join_room, leave_room, SocketIO
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# Configure application
app = Flask(__name__)
app.secret_key = "RequiredForFlashMessages"
socketio = SocketIO(app)
rooms = {}

@app.route("/")
def index():
    with sqlite3.connect("chatrooms.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM chatrooms")
        chatrooms = cursor.fetchmany(10)
        print(chatrooms)
        if not chatrooms:
            flash("No chatrooms available", category="primary")
            return render_template("index.html", session=session)

        user_id = None
        if session:
            user_id = session["user_id"]
        
        return render_template("index.html", session=session, chatrooms=chatrooms, user_id=user_id)
    return render_template("index.html", session=session)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # check for valid values
        if not username:
            flash("Username is required", category="danger")
            return render_template("register.html")
        if not password:
            flash("Password is required", category="danger")
            return render_template("register.html")
        if not confirmation:
            flash("Confirm Password is required", category="danger")
            return render_template("register.html")
        if password != confirmation:
            flash("Passwords don't match", category="danger")

        # generate password hash
        hash = generate_password_hash(password)

        try:
            with sqlite3.connect("chatrooms.db") as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", [username, hash])
                connection.commit()
                flash("You were successfully registered", category="success")

                # Query database for username
                cursor.execute("SELECT * FROM users WHERE username = ?", [username])
                data = cursor.fetchall()

                # Remember which user has logged in
                session["user_id"] = data[0][0]
                return redirect("/")
        except:
            flash("Username already exists", category="danger")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user id
    session.clear()

    # Redirect to homepage
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login user"""

    # forget any user id
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # check for valid values

        if not username:
            flash("Username is required", category="danger")
            return render_template("login.html")
        
        if not password:
            flash("Password is required", category="danger")
            return render_template("login.html")
        
        # query the database
        with sqlite3.connect("chatrooms.db") as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM users WHERE username = ?", [username])
            result = cursor.fetchall()

            # check if user exists
            if not result:
                flash("User doesn't exist", category="danger")
                return render_template("login.html")


            # check password hash
            hash = result[0][2]
            password_match = check_password_hash(hash, password)
            if not password_match:
                flash("Password is incorrect", category="danger")
                return render_template("login.html")
            

            # login the user
            session["user_id"] = result[0][0]
            return redirect("/")

    return render_template("login.html")



@app.route("/create_room", methods=["GET", "POST"])
def create_room():
    """Create chatroom"""

    if request.method == "POST":
        name = request.form.get("name")

        if not name:
            flash("Chatroom name is required")
        try:
            with sqlite3.connect("chatrooms.db") as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO chatrooms (chatroom, admin) VALUES (?, ?)", [name, session["user_id"]])
                rooms[name] = {"members": 0}
        except:
            flash("Chatroom already exists", category="danger")
            return render_template("create_room.html")

        return redirect("/")
    
    return render_template("create_room.html")




@socketio.on("connect")
def connect(auth):
    print(auth)
    print("connected")


@socketio.on("join_room")
def handle_join(data):
    room = data.get("room")
    print(room)

    if not room:
        return
    
    with sqlite3.connect("chatrooms.db") as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM chatrooms WHERE chatroom = ?", [room])
        room_query = cursor.fetchall()
        if not room_query:
            leave_room(room)
            return
        
        cursor.execute("SELECT * FROM users WHERE id = ?", [session["user_id"]])

        db_user = cursor.fetchone()
        db_user = db_user[1]
        print(db_user)

        join_room(room)

        print(room_query[0])

        cursor.execute("SELECT * FROM (SELECT * FROM chats WHERE chatroom_id = ? ORDER BY id DESC LIMIT 50) ORDER BY id ASC", [room_query[0][0]])

        chats = cursor.fetchall()

        if chats:
            for chat in chats:
                cursor.execute("SELECT * FROM users WHERE id = ?", [chat[2]])
                chat_user = cursor.fetchone()
                send({"name": chat_user[1], "message": chat[1], "user_id": chat[2], "timestamp": chat[4]+" +00:00"})

        print(chats)


        send({"name": db_user, "message": "has joined the room", "user_id": session["user_id"]}, to=room)
        # rooms[room]["members"] += 1
        print(f"{db_user} joined the room")






@socketio.on("leave_room")
def leave_room_manually(data):
    # todo: get current joined room name
    room = data.get("room")
    print("leave_room", room)

    if not room:
        return

    with sqlite3.connect("chatrooms.db") as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM chatrooms WHERE chatroom = ?", [room])

        room_query = cursor.fetchone()

        if not room_query:
            return

        leave_room(room)

        cursor.execute("SELECT * FROM users WHERE id = ?", [session["user_id"]])

        db_user = cursor.fetchone()
        db_user = db_user[1]
        print(db_user)

        send({"name": db_user, "message": "has left the room"}, to=room)
        # rooms[room]["members"] -= 1
        print(f"{db_user} left the room")




@socketio.on("new_message")
def new_message(data):
    msg = data.get("msg")
    room = data.get("room")

    if not room:
        return

    if not msg:
        return
    
    print(msg)

    with sqlite3.connect("chatrooms.db") as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM chatrooms WHERE chatroom = ?", [room])

        room_query = cursor.fetchone()

        if not room_query:
            return

        cursor.execute("SELECT * FROM users WHERE id = ?", [session["user_id"]])

        db_user = cursor.fetchone()
        db_user = db_user[1]
        print(db_user)
        
        send({"name": db_user, "message": msg, "user_id": session["user_id"]}, to=room)
        print(room_query[0])

        cursor.execute("INSERT INTO chats (message, user, chatroom_id) VALUES (?, ?, ?)", [msg, session["user_id"], room_query[0]])


        connection.commit()




@app.route("/delete", methods=["POST"])
def delete_room():
    """ Delete a room """

    if request.method == "POST":
        room = request.form.get("delete-room")
        print("delete-room", room)

        with sqlite3.connect("chatrooms.db") as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM chatrooms WHERE chatroom = ?", [room])
            room_id = cursor.fetchone()
            if not room_id:
                flash("Invalid room", category="danger")
                return redirect("/")
            
            room_admin = room_id[2]
            room_id = room_id[0]

            if room_admin != session["user_id"]:
                flash("Error: Cannot delete other user's room", category="danger")
                return redirect("/")

            cursor.execute("DELETE FROM chats WHERE chatroom_id = ?", [room_id])
            cursor.execute("SELECT * FROM chats WHERE chatroom_id = ?", [room_id])

            chats = cursor.fetchmany(10)

            if chats:
                flash("Failed to delete chatroom", category="danger")
                return redirect("/")

            cursor.execute("DELETE FROM chatrooms WHERE chatroom = ?", [room])
            cursor.execute("SELECT * FROM chatrooms WHERE chatroom = ?", [room])

            room_id = cursor.fetchone()

            if room_id:
                flash("Failed to delete chatroom", category="danger")
                return redirect("/")

    return redirect("/")




@app.route("/room=<roomname>", methods=["GET"])
def room(roomname):
    print(roomname)
    if not roomname:
        flash("Invalid room", category="danger")
        return render_template("room.html")

    with sqlite3.connect("chatrooms.db") as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM chatrooms WHERE chatroom = ?", [roomname])
        room_id = cursor.fetchone()

        if not room_id:
            flash("Room not found", category="danger")
            return render_template("room.html")

        print(room_id)
        room_id = room_id[0]
        print(room_id)

        cursor.execute("SELECT * FROM chats WHERE chatroom_id = ?", [room_id])
        messages = cursor.fetchall()

        if not messages:
            flash("This room doesn't contain any message", category="danger")
            return render_template("room.html")
        print(messages)

        msgs = []

        for message in messages:
            cursor.execute("SELECT * FROM users WHERE id = ?", [message[2]])
            username = (cursor.fetchone()[1],)
            message = message + username
            msgs.append(message)

    return render_template("room.html", messages=msgs, session=session)
