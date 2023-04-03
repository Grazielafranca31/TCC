from flask import Flask
app = Flask(__name__)

@app.route("/")

def gastos_deputados():
  return "olá"
