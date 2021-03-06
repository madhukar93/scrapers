import sqlite3
from ptap import logger
conn = sqlite3.connect('competitor_inventory_test1.db')
c = conn.cursor()

"""
product object
{
  "ps": [
    {
      "uid": "FOOCON0214822",   uid
      "dft": true,
      "sp": 10,                 sp
      "mrp": 10,                mrp
      "da": "55 GM",            unit
      "sst": "",
      "mxq": 6,
      "id": 214822
    }
  ],
  "typ": [
    "Sweet & Salty Biscuits"    subcat
  ],
  "tle": "Britannia 50-50 Maska Chaska" title
}
"""
try:
    c.execute(
        '''CREATE TABLE peppertap_product
           (
                uid text PRIMARY KEY,
                sp real,
                mrp real,
                title text,
                subcats text,
                category text,
                unit text
            )
        '''
    )
except sqlite3.OperationalError as inst:
    logger.error(
                    "{type}: {message}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                    )
                )

try:
    c.execute(
        '''CREATE TABLE peppertap_zone
           (
                zone_id int PRIMARY KEY,
                areas text,
                city text
            )
        '''
    )
except sqlite3.OperationalError as inst:
    logger.error(
                    "{type}: {message}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                    )
                )

try:
    c.execute(
        '''CREATE TABLE peppertap_zone_product_map
           (
                zone_id int,
                uid text,
                PRIMARY KEY (zone_id, uid),
                FOREIGN KEY(zone_id)
                    REFERENCES peppertap_zone(zone_id),
                FOREIGN KEY(uid)
                    REFERENCES peppertap_product(uid)
            )
        '''
    )
except sqlite3.OperationalError as inst:
    logger.error(
                    "{type}: {message}\n\t=====\n".format(
                        type=type(inst),
                        message=str(inst),
                    )
                )
