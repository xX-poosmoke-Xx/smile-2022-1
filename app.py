from flask import Flask, render_template, request
import sqlite3
from sqlite3 import Error


app = Flask(__name__)
DATABASE = "smile.db"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/')
def homer():
    return render_template("home.html")


@app.route('/menu')
def menu():
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, image, price FROM product"
    cur = con.cursor()
    cur.execute(query)

    product_list = cur.fetchall()
    con.close()
    return render_template("menu.html", products=product_list)


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('confirm_password')

    return render_template("signup.html")


if __name__ == '__main__':
    app.run()
