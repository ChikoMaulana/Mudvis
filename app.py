from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import certifi

import os
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

from os.path import join, dirname
from dotenv import load_dotenv

MONGODB_URI = os.environ.get('MONGO_DB_URI')
DB_NAME = os.environ.get("DB_NAME")

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = './static/uploads'

client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
db = client[DB_NAME]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        admin_user = db.admins.find_one({"username": username})
        
        if admin_user and check_password_hash(admin_user['password'], password):
            session['admin_username'] = admin_user['username']
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login'))
    
    return render_template("login.html")

@app.route("/logout")
def admin_logout():
    session.pop('admin_username', None)
    return redirect(url_for('login'))

@app.route("/tentang_kami")
def about():
    return render_template("tentang_kami.html")

@app.route("/produk")
def product():
    top_rated_products = list(db.products.find().sort("rating", -1).limit(3))
    return render_template("produk.html", top_rated_products=top_rated_products)

# @app.route("/semua_produk")
# def all_product():
#     products = list(db.products.find())
#     return render_template("semua_produk.html", products=products)

@app.route("/semua_produk")
def search():
    query = request.args.get('q', '')
    products = list(db.products.find({"name": {"$regex": query, "$options": "i"}})) if query else list(db.products.find())
    return render_template("semua_produk.html", products=products)

@app.route("/detail_produk/<product_id>")
def detail_product(product_id):
    product = db.products.find_one({"_id": ObjectId(product_id)})
    return render_template("detail_produk.html", product=product)

@app.route("/kontak", methods=["GET", "POST"])
def kontak():
    if request.method == "POST":
        contact_name = request.form["nama"]
        contact_email = request.form["email"]
        contact_message = request.form["pesan"]
        
        if contact_name or contact_email or contact_message:
            contact_data = {
                "name": contact_name,
                "email": contact_email,
                "message": contact_message
            }
            
            db.contact.insert_one(contact_data)
            
        return redirect(url_for('kontak'))
    else:
        return render_template("kontak.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if 'admin_username' in session:
        if request.method == "POST":
            product_name = request.form['productName']
            product_price = request.form['productPrice']
            product_description = request.form['productDescription']
            product_image = request.files['productImage']

            if product_image:
                filename = secure_filename(product_image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                product_image.save(filepath)

                product_data = {
                    'name': product_name,
                    'price': product_price,
                    'description': product_description,
                    'image': filepath
                }
                db.products.insert_one(product_data)

            return redirect(url_for('dashboard'))
        else:
            return render_template("data/upload.html")
    else:
        return redirect(url_for('login'))

@app.route("/edit/<product_id>", methods=["GET", "POST"])
def edit(product_id):
    if 'admin_username' in session:
        if request.method == "POST":
            product_name = request.form['productName']
            product_price = request.form['productPrice']
            product_description = request.form['productDescription']
            product_rating = request.form['productRating']
            product_image = request.files['productImage']

            product_data = {
                'name': product_name,
                'price': int(product_price),
                'description': product_description,
                'rating': float(product_rating)
            }

            if product_image:
                filename = secure_filename(product_image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                product_image.save(filepath)
                product_data['image'] = filepath

            db.products.update_one({'_id': ObjectId(product_id)}, {'$set': product_data})

            return redirect(url_for('detail_product', product_id=product_id))
        else:
            product = db.products.find_one({"_id": ObjectId(product_id)})
            return render_template("data/edit.html", product=product)
    else:
        return redirect(url_for('login'))
    
@app.route("/delete/<product_id>", methods=["GET", "POST"])
def delete(product_id):
    if 'admin_username' in session:
        if request.method == "POST":
            db.products.delete_one({'_id': ObjectId(product_id)})
            return redirect(url_for('dashboard'))
        else:
            product = db.products.find_one({"_id": ObjectId(product_id)})
            return render_template("data/delete.html", product=product)
    return redirect(url_for('login'))
    
@app.route("/dashboard")
def dashboard():
    if 'admin_username' in session:
        products = list(db.products.find())
        return render_template("data/dashboard.html", products=products)
    else:
        return redirect(url_for('login'))
    
@app.route("/admin_contact")
def admin_contact():
    if 'admin_username' in session:
        contacts = list(db.contact.find())
        return render_template("data/admin_contact.html", contacts=contacts)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)