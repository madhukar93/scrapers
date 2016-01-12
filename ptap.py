import requests
import json
import sqlite3
from rq import Queue
from redis import Redis
from unidecode import unidecode
import logging
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger('ptap')
logger.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('ptap_errors.log')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.error("===========reloaded==============")


class PepperTap:
    base_url = "https://api.peppertap.com"
    # should be imported from database connection file
    db_conn = sqlite3.connect('competitor_inventory_test1.db')

    def clear_table_data(self):
        self.db_cursor.execute(
            """
            DELETE FROM peppertap_product
            """
        )
        self.db_cursor.execute(
            """
            DELETE FROM peppertap_zone
            """
        )
        self.db_cursor.execute(
            """
            DELETE FROM peppertap_zone_product_map
            """
        )

    def _get_cities(self):
        cities_url = "/location/v1/cities/"
        response = requests.get(
            PepperTap.base_url + cities_url,
            verify=False
        )
        self.cities = [
            {'id': city['id'], 'name': city['name']}
            for city in response.json()
        ]

    def _get_areas(self):
        zones_url = "/location/v1/areas/"
        response = requests.get(
            PepperTap.base_url + zones_url,
            verify=False
        )
        self.areas = response.json()

    def _write_zones(self):
        zones = {}
        for area in self.areas:
            try:
                zones[area['zone_id']]['city'] = area['city']
                zones[area['zone_id']]['areas'].append(area['area'])
            except KeyError:
                zones[area['zone_id']] = {
                    'city': area['city'],
                    'areas': [area['area']]
                }
        self.zones = zones
        for zone_id, values in zones.iteritems():
            try:
                self._insert_zone(
                    (
                        zone_id,
                        ', '.join(values['areas']),
                        values['city']
                    )
                )
            except Exception as inst:
                logger.error(
                    "{type}: {message}: {data}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                        data=': '.join([str(zone_id), str(values)])
                    )
                )

    def _insert_zone(self, values):
        insert_query = "INSERT INTO peppertap_zone VALUES (?, ?, ?)"
        self.db_cursor.execute(
            insert_query,
            values
        )
        PepperTap.db_conn.commit()

    def _insert_product(self, values):
        insert_query = "INSERT INTO peppertap_product VALUES (?, ?, ?, ?, ?, ?, ?)"
        self.db_cursor.execute(
            insert_query,
            values
        )
        PepperTap.db_conn.commit()

    def _insert_product_zone_mapping(self, values):
        insert_query = "INSERT INTO peppertap_zone_product_map VALUES (?, ?)"
        self.db_cursor.execute(
            insert_query,
            values
        )
        PepperTap.db_conn.commit()

    def _get_categories(self, zone_id):
        categories_url = "/user/shop/categories/"
        response = requests.get(
            PepperTap.base_url + categories_url,
            params={'zone_id': zone_id},
            verify=False
        )
        return response.json()['categories']

    def __init__(self, *args, **kwargs):
        try:
            import setup_db_ptap
        except Exception as inst:
            logger.error(
                "{type}: {message}\n\t=====\n".format(
                    type=type(inst),
                    message=str(inst),
                )
            )
        self.db_cursor = PepperTap.db_conn.cursor()
        self._get_areas()
        self._write_zones()

    def get_products_by_category(self, category, zone_id):
        products_url = "/user/shop/{cid}/products/"
        params = {'zone_id': zone_id}
        response = requests.get(
            PepperTap.base_url + products_url.format(
                cid=category['id']
            ),
            params=params,
            verify=False
        )
        products = response.json()['pl']
        for product in products:
            try:
                self._insert_product(
                    (
                        product['ps'][0]['uid'],
                        product['ps'][0]['sp'],
                        product['ps'][0]['mrp'],
                        product['tle'],
                        ", ".join(product['typ']),
                        category['name'],
                        product['ps'][0]['da'],
                    )
                )
            except Exception as inst:
                logger.error(
                    "{type}: {message}: {data}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                        data=str(product)
                    )
                )
            try:
                self._insert_product_zone_mapping(
                    (
                        zone_id,
                        product['ps'][0]['uid'],
                    )
                )
            except Exception as inst:
                logger.error(
                    "{type}: {message}: {data}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                        data="product uid {}, zone_id {}".format(
                            product['ps'][0]['uid'], zone_id
                        )
                    )
                )

    def get_products_by_zone(self, zone_id):
        categories = self._get_categories(zone_id)
        for category in categories:
            for child_category in category['children']:
                # should be pushing this to the task queue
                self.get_products_by_category(child_category, zone_id)

    def get_all_products(self):
        for zone_id in self.zones.keys():
            get_products_by_zone(zone_id)
