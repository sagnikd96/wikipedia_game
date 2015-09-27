import sqlite3

with sqlite3.connect("sample.db") as connection:
    c = connection.cursor()
    c.execute("""CREATE TABLE posts(title TEXT, description TEXT)""")
    c.execute("""INSERT INTO posts VALUES("good", "I'm good")""")
    c.execute("""INSERT INTO posts VALUES("gooder", "I'm gooder")""")
