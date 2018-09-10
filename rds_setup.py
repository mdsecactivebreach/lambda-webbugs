#!/usr/bin/python
import sys
#import logging
import rds_config
import pymysql
import time

rds_host  = rds_config.db_endpoint
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = 3306

#logger = logging.getLogger()
#logger.setLevel(logging.INFO)

def rds_setup():
    with conn.cursor() as cur:
        cur.execute("create table webbug (bugID  int NOT NULL AUTO_INCREMENT, uid varchar(255) NOT NULL, ip varchar(255) NOT NULL, useragent TEXT, step int NOT NULL, dt DATETIME, PRIMARY KEY (bugID))")
        cur.execute("create table software (swID  int NOT NULL AUTO_INCREMENT, uid varchar(255) NOT NULL, ip varchar(255) NOT NULL, intip varchar(255) NOT NULL, useragent TEXT, software TEXT, dt DATETIME, PRIMARY KEY (swID))")
        conn.commit()
    print("SUCCESS: Inserted table structure")
    return

def insert_ping(uid, ip, useragent):
    try:
        with conn.cursor() as cur:
            query = """
            INSERT INTO `webbug` (bugId, uid, ip, useragent, dt)
            VALUES (DEFAULT, %s, %s, %s, %s)
            """
            foo = cur.execute(query, (uid, ip, useragent, time.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
    except Exception as e:
        print(e)


try:
    conn = pymysql.connect(rds_host, user=name,
                           passwd=password, db=db_name, connect_timeout=5)
except:
    print("ERROR: Unexpected error: Could not connect to MySql instance.")
    sys.exit()

print("SUCCESS: Connection to RDS mysql instance succeeded")

foo = rds_setup()
conn.close()