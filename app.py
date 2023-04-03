from flask import Flask

import requests
import pandas as pd
import json
!pip install datetime
from datetime import date
from datetime import datetime
import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import getpass
import requests

app = Flask(__name__)

@app.route("/")

def gastos_deputados():
  return "olá"
