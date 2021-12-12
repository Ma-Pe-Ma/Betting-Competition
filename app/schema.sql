-- Initialize the database.
-- Drop any existing data and create empty tables.

--DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS match;
DROP TABLE IF EXISTS match_bet;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS team;
DROP TABLE IF EXISTS team_bet;
DROP TABLE IF EXISTS group_bet;
DROP TABLE IF EXISTS final_bet;
-- DROP TABLE IF EXISTS post;

/*IF NOT EXISTS CREATE TABLE user (
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
  odd2 REAL,
  max_bet INTEGER
);

INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2, max_bet) VALUES ('2021-12-10 12:47', "A Csoport", "Magyarország", "Olaszország", 3, 2, 1.47, 2.1, 3.2, 50);
INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2, max_bet) VALUES ('2021-12-10 17:47', "B Csoport", "Németország", "Portugália", 3, 8, 1.57, 6.1, 1.2, 50);
INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2, max_bet) VALUES ('2021-12-10 15:47', "B Csoport", "Franci", "Angli", 1, 1, 1.57, 6.1, 1.2, 50);
INSERT INTO match (time, round, team1, team2, goal1, goal2, odd1, oddX, odd2, max_bet) VALUES ('2021-12-10 15:47', "B Csoport", "Franci", "Angli", 4, 9, 1.57, 6.1, 1.2, 50);


-- Table containing team details 
CREATE TABLE team (
  name TEXT NOT NULL PRIMARY KEY,
  hun_name TEXT,
  group_id CHAR,
  position INTEGER,
  top1 FLOAT,
  top2 FLOAT,
  top4 FLOAT,
  top16 FLOAT
);

INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("GERMANY", "Németország", 'A', 1, 2, 3, 4,2);
INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("HUNGARY", "Magyarország", 'A', 5, 6, 7, 8,4);
INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("ITALY", "Olaszország", 'A', 9, 10, 11, 12,1);
INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("JAPAN", "Japán", 'A', 13, 14, 15, 16,3);

INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("CZECHIA", "Csehország", 'B', 17, 18, 19, 20, 4);
INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("SLOVAKIA", "Szlovákia", 'B', 21, 22, 23, 24, 3);
INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("POLAND", "Lengyelország", 'B', 25, 26, 27, 28, 1);
INSERT INTO team(name, hun_name, group_id, top1, top2, top4, top16, position) VALUES("YUGOSLAVIA", "Jugoszlávia", 'B', 29, 30, 31, 32, 2);

-- Table holding a player's bet on a specific group
CREATE TABLE group_bet (
  id INTEGER NOT NULL PRIMARY KEY,
  group_ID INTEGER NOT NULL,
  username TEXT,
  bet INTEGER,
  FOREIGN KEY(username) REFERENCES user(username)
);

INSERT INTO group_bet(group_ID, username, bet) VALUES ("A", "MPM", 50);
INSERT INTO group_bet(group_ID, username, bet) VALUES ("B", "MPM", 11);

-- Table used by group bet, contains player's tip for the result of a team
CREATE TABLE team_bet (
  id INTEGER NOT NULL PRIMARY KEY,
  username TEXT,
  team TEXT,
  position INTEGER,
  FOREIGN KEY(username) REFERENCES user(username)
);

INSERT INTO team_bet(username, team, position) VALUES("MPM", "GERMANY",4);
INSERT INTO team_bet(username, team, position) VALUES("MPM", "HUNGARY",2);
INSERT INTO team_bet(username, team, position) VALUES("MPM", "ITALY",3);
INSERT INTO team_bet(username, team, position) VALUES("MPM", "JAPAN",1);

INSERT INTO team_bet(username, team, position) VALUES("MPM", "CZECHIA",4);
INSERT INTO team_bet(username, team, position) VALUES("MPM", "SLOVAKIA",3);
INSERT INTO team_bet(username, team, position) VALUES("MPM", "POLAND", 1);
INSERT INTO team_bet(username, team, position) VALUES("MPM", "YUGOSLAVIA",2);

-- Table containing the final bets
CREATE TABLE final_bet (
  id INTEGER NOT NULL PRIMARY KEY,
  username TEXT,
  team TEXT NOT NULL,
  bet INTEGER NOT NULL,
  result INTEGER NOT NULL,
  success INTEGER,
  FOREIGN KEY(username) REFERENCES user(username)
);

INSERT INTO final_bet(username, team, bet, result) VALUES("MPM", "GERMANY", 111, 1);

CREATE TABLE match_bet (
  id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  username TEXT,
  match_id INTEGER NOT NULL,
  goal1 INTEGER,
  goal2 INTEGER,
  bet INTEGER,
  FOREIGN KEY(username) REFERENCES user(username)
);

CREATE TABLE messages (
  label TEXT NOT NULL PRIMARY KEY,
  message TEXT
);

INSERT INTO match_bet (username, match_id, goal1, goal2, bet) VALUES ("MPM", 2, 3, 8, 14);
INSERT INTO match_bet (username, match_id, goal1, goal2, bet) VALUES ("MPM", 4, 4, 9, 27);
INSERT INTO match_bet (username, match_id, goal1, goal2, bet) VALUES ("MPM", 3, 4, 9, 27);

INSERT INTO messages (label, message) VALUES ("message1", "");
INSERT INTO messages (label, message) VALUES ("message2", "");
INSERT INTO messages (label, message) VALUES ("message3", "");
INSERT INTO messages (label, message) VALUES ("message4", "");
INSERT INTO messages (label, message) VALUES ("message5", "");

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