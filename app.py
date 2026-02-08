from datetime import date
from flask import Flask, render_template, request, redirect, Response, flash, session, url_for, jsonify
from flask_mysqldb import MySQL
import json
import requests
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'mysql.2425.lakeside-cs.org'
app.config['MYSQL_USER'] = 'student2425'
app.config['MYSQL_PASSWORD'] = 'ACSSE2425'
app.config['MYSQL_DB'] = '2425finalproject'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
app.secret_key = "OreoDog"


@app.route('/browse', methods=['GET'])
def browse():
    if request.method == 'GET':
        # Get a list of all expansion sets and their codes
        jsonSets = requests.get("https://api.scryfall.com/sets").json()["data"]
        sets = []
        for setObject in jsonSets:
            if setObject["set_type"] == "expansion":
                sets.append((setObject["name"], setObject["code"]))
        
        return render_template("filter.html.j2", sets=sets, username=session.get("zubit_username"))


@app.route('/filter', methods=['GET'])
def filter():
    # Start a search string for the Scryfall API
    q = ""
    card_type= request.values.get("type")
    if card_type:
        q += "type%3A" + card_type + "+"
    cmc = request.values.get("cmc")
    if cmc:
        q += "cmc%3D" + cmc + "+"
    rarity = request.values.get("rarity")
    if rarity:
        q += "rarity%3A" + rarity
        q += "+"
    sets = request.values.getlist("set")
    if len(sets) > 0:
        q += "%28"
        for set_name in sets:
            q += "set%3A" + set_name
            q += "+OR+"
        q = q.rstrip("+OR+")
        q += "%29+"
    colors = request.values.getlist("color")
    if colors:
        q += "color%3D"
        for color in colors:
            q += color
        q += "+"
    cardText = request.values.get("cardText")
    if cardText:
        words = cardText.split(" ")
        for word in words:
            q += "oracle%3A" + word + "+"
    
    q = q.rstrip("+")
    if len(q) == 0:
        flash("Must apply some number of filters.", "danger")
        return redirect(url_for("browse"))
    url = "https://api.scryfall.com/cards/search"+"?q=" + q
    
    sort = request.values.get("sort")
    if sort:
        url += "&order="+sort
    else:
        sort = "name"

    arrow = "&rarr;"
    dir = request.values.get("dir")
    if dir:
        url += "&dir=" + dir
        if dir == "desc":
            arrow = "&larr;"
    else:
        url += "&dir=" + "asc"

    cards = requests.get(url).json()
    try:
        cardData = cards["data"]
    except:
        cardData = []
    return render_template("cardlist.html.j2", cards=cardData, sortValue=sort, arrow=arrow, username=session.get("zubit_username"))


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html.j2", username=session.get("zubit_username"))


@app.route('/search')
def search():
    return render_template("search.html.j2", username=session.get("zubit_username"))


@app.route('/cards')
def cards():
    cardName = request.values.get("name")
    card = requests.get("https://api.scryfall.com/cards/named", {"exact": cardName}).json()
    if card["object"] == "error":
        flash("Invalid card.", "danger")
        return redirect(url_for('/'))
    username = session.get("zubit_username")
    if username:
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM zubit_decks d JOIN zubit_users u ON d.user_id = u.id WHERE u.username = %s;"
        queryValues = (username,)
        cursor.execute(query, queryValues)

        mysql.connection.commit()
        data = cursor.fetchall()
    else:
        data = []

    return render_template("card.html.j2", card=card, username=session.get("zubit_username"), decks=data)


@app.route('/autocomplete', methods=["POST"])
def autocomplete():
    cardName = request.values.get("cardName")
    response = requests.get("https://api.scryfall.com/cards/autocomplete", {"q": cardName}).json()

    values = response["data"][:10]
    if len(values) == 0:
        return ''

    identifiers = []
    for card in values:
        identifiers.append({"name": card})

    cardData = requests.post("https://api.scryfall.com/cards/collection", headers={"Content-Type": "application/json"}, json={"identifiers": identifiers}).json()["data"]
    return cardData


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html.j2", username=session.get("zubit_username"))
    else:
        username = request.values.get("username")
        password = request.values.get("password")
        confirmPassword = request.values.get("confirmPassword")
        
        if password != confirmPassword:
            flash("Passwords don't match.", "danger")
            return redirect(url_for("signup"))
        
        passwordHash = generate_password_hash(password)

        cursor = mysql.connection.cursor()

        query = "SELECT * FROM zubit_users WHERE username=%s;"
        queryValues = (username,)

        cursor.execute(query, queryValues)
        mysql.connection.commit()

        data = cursor.fetchall()
        if len(data) > 0:
            flash("There already exists a user with that username. Please try again.")
            return redirect(url_for("signup"))

        query = "INSERT INTO zubit_users (username, password) VALUES (%s, %s);"
        queryValues = (username, passwordHash)

        cursor.execute(query, queryValues)
        mysql.connection.commit()

        session["zubit_username"] = username

        flash(f"You have successfully signed up, {username}!", "success")
        return redirect(url_for('/'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="GET":
        return render_template("login.html.j2", username=session.get("zubit_username"))
    else:
        username = request.values.get("username")
        password = request.values.get("password")

        cursor = mysql.connection.cursor()

        query = "SELECT * FROM zubit_users WHERE username = %s;"
        queryValues = (username,)
        
        cursor.execute(query, queryValues)
        mysql.connection.commit()

        data = cursor.fetchone()
        if not data:
            flash("There is no user with that username.", "danger")
            return redirect(url_for("login"))

        passwordHash = data["password"]

        if not check_password_hash(passwordHash, password):
            flash("Incorrect password.", "danger")
            return redirect(url_for("login"))
        session["zubit_username"] = username

        flash(f"You have successfully logged in, {username}!", "success")
        return redirect(url_for("index"))


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("zubit_username", None)
    flash(f"You have been logged out!", "success")
    return redirect(url_for("index"))


@app.route("/decks", methods=["GET", "POST"])
def decks():
    if request.method == "GET":
        username = session.get("zubit_username")
        if not username:
            flash("Please log in to create a deck.", "danger")
            return redirect(url_for("login"))
        
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM zubit_decks d JOIN zubit_users u ON d.user_id = u.id WHERE u.username=%s;"
        queryValues = (username,)
        
        cursor.execute(query, queryValues)
        mysql.connection.commit()
        data = cursor.fetchall()
        
        identifiers = []
        for deck in data:
            identifiers.append({"oracle_id": deck["cover_card_id"]})
        
        if len(identifiers) == 0:
            return render_template("decklist.html.j2", deckData=[], username=session.get("zubit_username"))
        cardData = requests.post("https://api.scryfall.com/cards/collection", headers={"Content-Type": "application/json"}, json={"identifiers": identifiers}).json()["data"]
        
        deckData = []
        for i in range(len(data)):
            deckDict = {}
            deckDict["cover_image"] = cardData[i]["image_uris"]["art_crop"]
            deckDict["name"] = data[i]["name"]
            deckDict["format"] = data[i]["format"]
            deckData.append(deckDict)
        return render_template("decklist.html.j2", deckData=deckData, username=session.get("zubit_username"))
    else:
        username = session.get("zubit_username")
        if not username:
            flash("Please log in to create a deck.", "danger")
            return redirect(url_for("login"))
        cursor = mysql.connection.cursor()

        query = "SELECT * FROM zubit_decks d JOIN zubit_users u ON d.user_id = u.id WHERE u.username=%s;"
        queryValues = (username,)
        cursor.execute(query, queryValues)
        mysql.connection.commit()
        data = cursor.fetchall()
        name = "New Deck"
        number = 0
        while True:
            unique = True
            for deck in data:
                if deck["name"] == name:
                    unique = False
                    break
            if unique:
                break
            number += 1
            name = "New Deck (" + str(number) + ")"

        cover = "a3fb7228-e76b-4e96-a40e-20b5fed75685"
        deckFormat = "vintage"
        query = "INSERT INTO zubit_decks (user_id, name, format, cover_card_id) VALUES ((SELECT id FROM zubit_users WHERE username=%s), %s, %s, %s);"
        queryValues = (username, name, deckFormat, cover)

        cursor.execute(query, queryValues)
        mysql.connection.commit()
        
        flash(f"{name} has been created.", "info")
        return redirect(url_for("decks"))


@app.route("/deck")
def deck():
    deckName = request.values.get("name")
    username = session.get("zubit_username")
    if not username:
        flash("Please log in to create a deck.", "danger")
        return redirect(url_for("login"))
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM zubit_decks d JOIN zubit_users u ON d.user_id = u.id WHERE u.username = %s AND d.name = %s;"
    queryValues = (username, deckName)

    cursor.execute(query, queryValues)
    mysql.connection.commit()
    
    data = cursor.fetchone()
    if len(data) < 1:
        flash("Deck does not exist.", "danger")
        return redirect(url_for("decks"))
    deckId = data["id"]
    deckFormat = data["format"]

    query = "SELECT card_id, quantity FROM zubit_cards WHERE deck_id = %s;"
    queryValues = (deckId,)

    cursor.execute(query, queryValues)
    mysql.connection.commit()

    data = cursor.fetchall()

    identifiers = []
    for card in data:
        identifiers.append({"oracle_id": card["card_id"]})
        
    if len(identifiers) == 0:
        return render_template("deck.html.j2", cardData=[], username=session.get("zubit_username"))
    
    scryfallData = requests.post("https://api.scryfall.com/cards/collection", headers={"Content-Type": "application/json"}, json={"identifiers": identifiers}).json()["data"]
    cardData = {"Creatures": [0], "Planeswalkers": [0], "Spells": [0], "Artifacts": [0], "Enchantments": [0], "Lands": [0]}
    numCards = 0
    allLegal = True
    totalPrice = 0
    for i in range(len(data)):
        cardDict = {}
        cardDict["image"] = scryfallData[i]["image_uris"]["normal"]
        cardDict["name"] = scryfallData[i]["name"]
        cardDict["price"] = scryfallData[i]["prices"]["usd"]
        cardDict["quantity"] = data[i]["quantity"]
        if cardDict["price"]:
            totalPrice += float(cardDict["price"]) * cardDict["quantity"]
        numCards += cardDict["quantity"]
        cardDict["mana_cost"] = scryfallData[i]["mana_cost"]
        
        type_line = scryfallData[i]["type_line"]
        if "Land" in type_line:
            cardData["Lands"].append(cardDict)
            cardData["Lands"][0] += cardDict["quantity"]
        elif "Instant" in type_line or "Sorcery" in type_line:
            cardData["Spells"].append(cardDict)
            cardData["Spells"][0] += cardDict["quantity"]
        elif "Planeswalker" in type_line:
            cardData["Planeswalkers"].append(cardDict)
            cardData["Planeswalkers"][0] += cardDict["quantity"]
        elif "Creature" in type_line:
            cardData["Creatures"].append(cardDict)
            cardData["Creatures"][0] += cardDict["quantity"]
        elif "Artifact" in type_line:
            cardData["Artifacts"].append(cardDict)
            cardData["Artifacts"][0] += cardDict["quantity"]
        elif "Enchantment" in type_line:
            cardData["Enchantments"].append(cardDict)
            cardData["Enchantments"][0] += cardDict["quantity"]

        if scryfallData[i]["legalities"][deckFormat] != "legal":
            if scryfallData[i]["legalities"][deckFormat] == "restricted":
                if cardDict["quantity"] > 1:
                    allLegal = False
            else:
                allLegal = False
    
    return render_template("deck.html.j2", cardData=cardData, deckName=deckName, deckFormat=deckFormat, numCards=numCards, allLegal=allLegal, totalPrice = totalPrice, username=session.get("zubit_username"))


@app.route('/addToDeck', methods=["POST"])
def addToDeck():
    cardName = request.values.get("cardName")
    deckId = request.values.get("deck")
    quantity = int(request.values.get("quantity"))
    
    card = requests.get("https://api.scryfall.com/cards/named", {"exact": cardName}).json()

    cursor = mysql.connection.cursor()

    query = "SELECT * FROM zubit_cards WHERE card_id = %s and deck_id = %s;"
    queryValues = (card["oracle_id"], deckId)

    cursor.execute(query, queryValues)
    mysql.connection.commit()

    data = cursor.fetchone()

    if data:
        if data["quantity"] + quantity > 4 and "Basic Land" not in card["type_line"]:
            flash("Too many copies of that card already in deck. Only four of each card are allowed other than basic lands.", "danger")
            return redirect(request.referrer)
        query = "UPDATE zubit_cards SET quantity = %s WHERE id = %s;"
        updatedRow = data["id"]
        queryValues = (data["quantity"] + quantity, updatedRow)

        cursor.execute(query, queryValues)
        mysql.connection.commit()
    else:
        if quantity > 4 and "Basic Land" not in card["type_line"]:
            flash("Too many copies of that card already in deck. Only four of each card are allowed other than basic lands.", "danger")
            return redirect(request.referrer)
        query = "INSERT INTO zubit_cards (card_id, deck_id, quantity) VALUES (%s, %s, %s);"
        queryValues = (card["oracle_id"], deckId, quantity)

        cursor.execute(query, queryValues)
        mysql.connection.commit()
        updatedRow = cursor.lastrowid

    query = "UPDATE zubit_decks d JOIN zubit_cards c ON d.id = c.deck_id SET cover_card_id = %s WHERE c.id = %s;"
    queryValues = (card["oracle_id"], updatedRow)

    cursor.execute(query, queryValues)
    mysql.connection.commit()

    flash(f"Successfully added to deck!", "success")
    return redirect("/decks")


@app.route('/changeFormat', methods=["POST"])
def changeFormat():
    deckName = request.values.get("deckName")
    newFormat = request.values.get("format")
    
    username = session.get("zubit_username")
    if not username:
        return {"message": "You are not logged in.", "type": "danger"}

    if newFormat.capitalize() not in ["Standard", "Alchemy", "Explorer", "Timeless", "Pioneer", "Modern", "Legacy", "Vintage", "Pauper"]:
        return {"message": "Invalid format.", "type": "danger"}

    cursor = mysql.connection.cursor()
    query = "UPDATE zubit_decks d JOIN zubit_users u ON d.user_id = u.id SET format=%s WHERE d.name=%s AND u.username=%s;"
    queryValues = (newFormat, deckName, username)

    cursor.execute(query, queryValues)
    mysql.connection.commit()

    return {"message": f"Changed format of {deckName} to {newFormat.capitalize()}!", "type": "success"}


@app.route('/changeName', methods=["POST"])
def changeName():
    deckName = request.values.get("deckName")
    newName = request.values.get("newName")
    
    username = session.get("zubit_username")
    if not username:
        flash("You are not logged in.", "danger")
        return ''

    cursor = mysql.connection.cursor()

    query = "SELECT * FROM zubit_decks d JOIN zubit_users u ON d.user_id = u.id WHERE u.username=%s AND d.name=%s;"
    queryValues = (username, newName)

    cursor.execute(query, queryValues)
    mysql.connection.commit()

    data = cursor.fetchall()
    if data:
        flash("You already have a deck with that name.", "danger")
        return ''

    query = "UPDATE zubit_decks d JOIN zubit_users u ON d.user_id = u.id SET d.name=%s WHERE d.name=%s AND u.username=%s;"
    queryValues = (newName, deckName, username)
    try:
        cursor.execute(query, queryValues)
    except:
        flash("stop")
        return ''
    mysql.connection.commit()

    flash(f"Changed name of {deckName} to {newName}!", "success")
    return ''


@app.route("/exportToArena", methods=["POST"])
def exportToArena():
    deckName = request.values.get("deckName")
    
    username = session.get("zubit_username")
    if not username:
        return {"message": "You are not logged in.", "type": "danger", "exportString": ""}

    cursor = mysql.connection.cursor()
    query = "SELECT * FROM zubit_cards c JOIN zubit_decks d ON c.deck_id = d.id JOIN zubit_users u ON d.user_id = u.id WHERE u.username=%s AND d.name=%s;"
    queryValues = (username, deckName)

    cursor.execute(query, queryValues)
    mysql.connection.commit()
    data = cursor.fetchall()

    if not data:
        return {"message": "Copied to clipboard!", "type": "success", "exportString": ""}

    identifiers = []
    for card in data:
        identifiers.append({"oracle_id": card["card_id"]})
    
    scryfallData = requests.post("https://api.scryfall.com/cards/collection", headers={"Content-Type": "application/json"}, json={"identifiers": identifiers}).json()["data"]

    exportString = "Deck"
    for i in range(len(data)):
        exportString += "\n" + str(data[i]["quantity"]) + " " + scryfallData[i]["name"]
    
    return {"message": "Copied to clipboard!", "type": "success", "exportString": exportString}