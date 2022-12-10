import os
import sqlite3

script_path = os.path.dirname(os.path.realpath(__file__))
conn = sqlite3.connect(script_path + '/data.db')
c = conn.cursor()

class DataBase:
    @classmethod
    def GetFromDB(self):
        with conn:
            c.execute("SELECT * FROM projects")
            return c.fetchall()

    @classmethod
    def GoToDB(self, url):
        with conn:
            c.execute(f"INSERT INTO 'main'.'projects'('id','url') VALUES (NULL, ?)", (url, ))
    
    @classmethod
    def Status(self, url):
        with conn:
            c.execute(f"SELECT url FROM projects WHERE url = ?", (url, ))
            if len(c.fetchall()) == 0:
                return False
            else:
                return True