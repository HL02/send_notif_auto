from flask import Flask, render_template, redirect, url_for, request,session, flash, current_app,send_file
from flask.cli import with_appcontext
import requests,bs4,re
from wtforms import Form, StringField, SelectField
from flask_session import Session
from binance.client import Client
import sqlite3
import os
import logging
import pandas as pd
from datetime import datetime as dt
from math import isclose
import time
from discord_webhook import DiscordWebhook, DiscordEmbed

logging.basicConfig(level=logging.INFO)

app=Flask(__name__)
app.config['SESSION_PERMANENT']=False
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='thuhienluuthi'
webhook_url=''

def createTable():
    conn=sqlite3.connect('ResultDB.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS crypto
             ([Alert_ID] INTEGER PRIMARY KEY AUTOINCREMENT, [Currency] text,
             [Symbol_Name] text, [Price] real, [Status] integer,
             [Date] date)''')
    c.close
    conn.close()

def insertData(currency, symbolName, Price):
    conn = sqlite3.connect('ResultDB.db')
    c = conn.cursor()
    c.execute('''INSERT INTO crypto (Currency, Symbol_Name, Price, Status, Date) VALUES (?, ?, ?, 1, ?)''',(currency, symbolName, Price, dt.now()))
    conn.commit()
    c.close
    conn.close()
    
def createLoginData():
    conn=sqlite3.connect('Login.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS LOGIN
             ([Alert_ID] INTEGER PRIMARY KEY AUTOINCREMENT, [User_Name] text not null,
             [Password] text not null)''')
    c.close
    conn.close()

createLoginData()

def check_user(username,password):
    conn=sqlite3.connect('Login.db')
    c=conn.cursor()
    c.execute('''SELECT * FROM LOGIN WHERE User_Name=? AND Password=?''',(username,password))
    loginData=c.fetchone()
    if loginData or (username=='hien.luu2304' and password=='thuhienluuthi'):
        return True
    else:
        return False
    
@app.route('/')
def home():
    return render_template('index.html')

s=None
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    error=None
    if request.method == 'POST':
        session['user_name']=request.form['username']
        session['password']=request.form['password']
        if check_user(session['user_name'],session['password']):
            global s
            s=1
            return redirect(url_for('database'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        session['User_Name']=request.form['username']
        session['Password']=request.form['password']
        userName=session['User_Name']
        password=session['Password']
        conn = sqlite3.connect('Login.db')
        c = conn.cursor()
        c.execute('''INSERT INTO LOGIN (User_Name, Password) VALUES (?, ?)''',(userName, password))
        conn.commit()
        c.close
        conn.close()
        return redirect(url_for('home'))
    return render_template('signup.html')

createTable()

@app.route('/inputdata', methods=['GET', 'POST'])
def inputdata():
    if request.method == 'POST':
        session['Currency']=request.form['currency']
        session['Symbol Name']=request.form['symbol_name']
        session['Price']=request.form['price']
        currency=session['Currency']
        symbolName=session['Symbol Name']
        Price=session['Price']
        insertData(currency, symbolName, Price)
        return redirect(url_for('inputdata1'))
    return render_template('input_data1.html')
@app.route('/inputdata1', methods=['GET', 'POST'])
def inputdata1():
    if request.method == 'POST':
        session['Currency']=request.form['currency']
        session['Symbol Name']=request.form['symbol_name']
        session['Price']=request.form['price']
        currency=session['Currency']
        symbolName=session['Symbol Name']
        Price=session['Price']
        insertData(currency, symbolName, Price)
        return redirect(url_for('inputdata'))
    return render_template('input_data1.html')

@app.route('/database')
def database():
    conn = sqlite3.connect('ResultDB.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute("SELECT * FROM crypto")
    content=cur.fetchall()
    global s
    admin=session.get('user_name')
    password=session.get('password')
    return render_template("database.html",content=content,s=s,admin=admin, password=password)

@app.route('/logindatabase')
def logindatabase():
    conn = sqlite3.connect('Login.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute("SELECT * FROM LOGIN")
    content=cur.fetchall()
    admin=session.get('user_name')
    password=session.get('password')
    return render_template("logindatabase.html",content=content,admin=admin,password=password)

@app.route('/delete', methods=['GET', 'POST'])
def delete():   
    conn = sqlite3.connect('ResultDB.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    if request.method == 'POST': 
        for getid in request.form.getlist('mycheckbox'):
            print(getid)
            cur.execute('DELETE FROM crypto WHERE Alert_ID = {0}'.format(getid))
            conn.commit()
        flash('Successfully Deleted!')
    cur.close
    conn.close()
    return redirect('/database')

@app.route('/deletelogindatabase', methods=['GET', 'POST'])
def deletelogindatabase():   
    conn = sqlite3.connect('Login.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    if request.method == 'POST': 
        for getid in request.form.getlist('mycheckbox'):
            print(getid)
            cur.execute('DELETE FROM LOGIN WHERE Alert_ID = {0}'.format(getid))
            conn.commit()
        flash('Successfully Deleted!')
    cur.close
    conn.close()
    return redirect('/logindatabase')

@app.route('/exit')
def exit():
    session.pop('user_name',None)
    session.pop('password',None)
    global s
    s=None
    return redirect(url_for('home'))
    return render_template('exit.html')

def getPrice():
    client = Client('jOKZmwYvRKVlh3M8FEnZ6z8t58VYpflL1v6rhV7tNTCmjKbXuytkOH5rinjKeLsw', 'zk7zwkZJJf9CmIalQ3ggRNWn2O8miKiWVa0mfxrQztVqFo0Cd4i15bDKXpvyiC1H')
    prices = client.get_all_tickers()
    result=kiemTraGiaTickerTrongDatabase(prices)
    return result

def kiemTraGiaTickerTrongDatabase(prices):
    conn = sqlite3.connect('ResultDB.db')
    c = conn.cursor()
    sor = list(c.execute('''SELECT * FROM crypto WHERE status = 1'''))
    for i in prices:
        for x in range(len(sor)):
            symbol = sor[x][2]+sor[x][1]
            if sor[x][2]+sor[x][1] == i['symbol']:
                if isclose(float(i['price']), sor[x][3], abs_tol=float(i['price'])*5/100):
                    global webhook_url
                    message = "**📢 Price Alert!**\n" \
                        f"🔹 **Price of `{sor[x][2]}` is near our target!**\n\n" \
                        f"💰 **Target Price:** `{round(float(sor[x][3]),2)}` `{sor[x][1]}`\n" \
                        f"📉 **Current Price:** `{round(float(i['price']),2)}` `{sor[x][1]}`\n" \
                        f"⚡ **Gaps:** `{round(float(sor[x][3]) - float(i['price']),2)}` `{sor[x][1]}`\n" \
                        
                    webhook=DiscordWebhook(url=webhook_url,content=message)
                    webhook.execute()
                    c.execute('''UPDATE crypto SET status= 0 WHERE Alert_ID= ?''',(sor[x][0],))
                    conn.commit()
                else:
                    pass
    c.close
    conn.close()
@app.route('/checkPrice')
def checkPrice():
    while True:
        getPrice()
        time.sleep(10)

if __name__=='__main__':
    app.run(debug=True)
