import MySQLdb
import os

def init_database(user, password):
    db = MySQLdb.connect(user=user, password=password, host='localhost')
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS instatracker")

    db.select_db("instatracker")
    cursor = db.cursor()

    cursor.execute("DROP TABLE IF EXISTS followers"
                   "CREATE TABLE IF NOT EXISTS followers ("
                   "id bigint(22) UNSIGNED NOT NULL AUTO_INCREMENT,"
                   "username varchar(255) NOT NULL,"
                   "userid varchar(255) NOT NULL,"
                   "follows varchar(255) NOT NULL,"
                   "day DATETIME NOT NULL,"
                   "PRIMARY KEY (id)"
                   ")")

    cursor.execute("DROP TABLE IF EXISTS profile"
                   "CREATE TABLE IF NOT EXISTS profile ("
                   "id bigint(22) UNSIGNED NOT NULL AUTO_INCREMENT,"
                   "username varchar(255) NOT NULL,"
                   "pfp text NOT NULL,"
                   "userid varchar(255) NOT NULL,"
                   "PRIMARY KEY (id)"
                   ")")

    db.close()


if __name__ == '__main__':
    USER = os.getenv('db_user')
    PASSWORD = os.getenv('db_password')
    init_database(USER, PASSWORD)
