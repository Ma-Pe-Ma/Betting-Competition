-- Initialize the database.
-- Drop any existing data and create empty tables.

--DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS match;
DROP TABLE IF EXISTS match_bets;
DROP TABLE IF EXISTS messages;
-- DROP TABLE IF EXISTS post;

/*CREATE TABLE user (
  username TEXT UNIQUE NOT NULL PRIMARY KEY,
  name TEXT NOT NULL,
  password TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  reminder INTEGER NOT NULL,
  admin BOOLEAN
);*/

CREATE TABLE match (
  id INTEGER NOT NULL PRIMARY KEY,
  time TEXT NOT NULL,
  round TEXT,
  team1 TEXT NOT NULL,
  team2 TEXT NOT NULL,
  goal1 INTEGER,
  goal2 INTEGER,
  odd1 REAL,
  oddX REAL,
  odd2 REAL
);

INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2) VALUES ('2021-07-29 12:47', "A Csoport", "Magyarország", "Olaszország", 3, 2, 1.47, 2.1, 3.2);
INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2) VALUES ('2021-07-29 17:47', "B Csoport", "Németország", "Portugália", "", "", 1.57, 6.1, 1.2);
INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2) VALUES ('2021-07-30 17:47', "B Csoport", "Franci", "Angli", "", "", 1.57, 6.1, 1.2);

CREATE TABLE match_bets (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  match_id INTEGER NOT NULL,
  goal1 INTEGER,
  goal2 INTEGER,
  bet INTEGER
);

CREATE TABLE messages (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  message TEXT
);

INSERT INTO match_bets (username, match_id, goal1, goal2, bet) VALUES ("MPM", 1, 1, 2, 14);
INSERT INTO match_bets (username, match_id, goal1, goal2, bet) VALUES ("MPM", 2, 3, 9, 27);

INSERT INTO messages (message) VALUES ("Itt egy üzi!");

/*CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);*/

/*https://stackoverflow.com/questions/10950362/protecting-against-sql-injection-in-python
https://docs.python.org/3/library/sqlite3.html*/