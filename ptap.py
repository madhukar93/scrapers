import requests
import json
import sqlite3
from rq import Queue
from redis import Redis
from unidecode import unidecode
import logging


class PepperTap:
    base_url = "https://api.peppertap.com"

    def _get_cities(self):
        requests.get()
