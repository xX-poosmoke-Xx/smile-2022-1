from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from datetime import datetime
import smtplib, ssl
from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



app = Flask(__name__)
DATABASE = "smile.db"
app.secret_key = "jittrippin"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    if session.get('email') is None:
        print('logged out')
        return False
    else:
        print('logged in')
        return True


@app.route('/')
def homer():
    return render_template("home.html")


@app.route('/menu')
def menu():
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, image, price, id FROM product"
    cur = con.cursor()
    cur.execute(query)

    product_list = cur.fetchall()
    con.close()
    return render_template("menu.html", products=product_list, logged_in=is_logged_in())


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email')
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = 'SELECT id, first_name FROM users WHERE email=? AND password=?'
        cur = con.cursor()
        cur.execute(query, (email, password))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            print(user_id, first_name)

            session['email'] = email
            session['userid'] = user_id
            session['first_name'] = first_name

            return redirect("/menu")

        else:
            return redirect("/login?error=Incorrect+username+or+password")

    return render_template("login.html")


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        print(request.form)
        first_name = request.form.get('first_name').title().strip()
        surname = request.form.get('surname').title().strip()
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('confirm_password')

        if password != password2:
            return redirect("/signup?error=Please+make+password+match")

        if len(password) < 8:
            return redirect("/signup?error=Please+make+password+at+least+8+characters")

        con = create_connection(DATABASE)

        query = "INSERT INTO users (first_name, surname, email, password) VALUES (?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query, (first_name, surname, email, password))
        con.commit()
        con.close()

    error = request.args.get('error')
    if error == None:
        error = ""

    return render_template("signup.html", error=error)


@app.route('/addtocart/<product_id>')
def addtocart(product_id):
    print("Added product if {} to the cart".format(product_id))
    customer_id = session['userid']
    timestamp = datetime.now()

    query = "INSERT INTO cart (customerid, productid, timestamp) VALUES (?, ?, ?)"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (customer_id, product_id, timestamp))

    try:
        cur.execute(query, (customer_id, product_id, timestamp))
    except sqlite3.IntegrityError as e:
        print(e)
        print("### PROBLEM INSERTING INTO DATABASE - FOREIGN KEY ###")
        con.close()
        return redirect('/menu?error=something+went+very+very+wrong')

    con.commit()
    con.close()

    return redirect(request.referrer)


@app.route('/cart')
def cart():
    if not is_logged_in():
        return redirect('/menu')
    else:
        customerid = session['userid']
        query = "SELECT productid FROM cart WHERE customerid=?;"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (customerid,))
        product_ids = cur.fetchall()
        print(product_ids)

        for i in range(len(product_ids)):
            product_ids[i] = product_ids[i][0]
        print(product_ids)

        unique_product_ids = list(set(product_ids))
        for i in range(len(unique_product_ids)):
            product_count = product_ids.count(unique_product_ids[i])
            unique_product_ids[i] = [unique_product_ids[i], product_count]
        print(unique_product_ids)
        total = 0
        query = "SELECT name, price FROM product WHERE id = ?"
        for item in unique_product_ids:
            cur.execute(query, (item[0], ))
            item_details = cur.fetchall()
            print(item_details)
            item.append(item_details[0][0])
            item.append(item_details[0][1])
            item.append(item[1] * item[3])
            print(item)
            total += item[4]

        con.close()
        return render_template("cart.html", cart_data=unique_product_ids, logged_in=is_logged_in())


@app.route('/removeonefromcart/<product_id>')
def remove_from_cart(product_id):
    print('Remove: {}'.format(product_id))
    customer_id = session['userid']
    query = "DELETE FROM cart WHERE id=(SELECT MIN(id) FROM cart WHERE productid=? and customerid=?);"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (product_id, customer_id))
    con.commit()
    con.close()
    return redirect('/cart')


@app.route('/confirmorder')
def confirmorder():
    customer_id = session['userid']
    con = create_connection(DATABASE)
    cur = con.cursor()
    query = "DELETE FROM cart WHERE customerid=?;"
    cur.execute(query, (customer_id, ))
    con.commit()
    con.close()
    return redirect('/?message=Order+complete')


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


if __name__ == '__main__':
    app.run()
