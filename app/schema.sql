-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS match_bet;
DROP TABLE IF EXISTS final_bet;
DROP TABLE IF EXISTS team_bet;
DROP TABLE IF EXISTS group_bet;
DROP TABLE IF EXISTS team_translation;
DROP TABLE IF EXISTS team;
DROP TABLE IF EXISTS match;
DROP TABLE IF EXISTS bet_user;

-- Table containing user data
CREATE TABLE bet_user (
  username TEXT UNIQUE NOT NULL PRIMARY KEY,
  password TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  reminder INTEGER NOT NULL,  -- 0: on days when there is a match on which betting did not happen, 1: every match day, 2: no reminder
  summary INTEGER NOT NULL,
  timezone TEXT NOT NULL, 
  language TEXT NOT NULL,
  admin BOOLEAN
);

-- Table containing match data
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

-- Table containing team details 
CREATE TABLE team (
  name TEXT NOT NULL PRIMARY KEY,
  group_id CHAR,
  position INTEGER,
  top1 FLOAT,
  top2 FLOAT,
  top4 FLOAT,
  top16 FLOAT
);

-- Table containing team name translations
CREATE TABLE team_translation (
  id SERIAL PRIMARY KEY,
  name TEXT,
  language TEXT,
  translation TEXT
);

-- Table holding a player's bet on a specific group
CREATE TABLE group_bet (
  id SERIAL PRIMARY KEY,
  group_ID TEXT NOT NULL,
  username TEXT,
  bet INTEGER,
  FOREIGN KEY(username) REFERENCES bet_user(username)
);

-- Table used by group bet, contains player's tip for the result of a team
CREATE TABLE team_bet (
  id SERIAL PRIMARY KEY,
  username TEXT,
  team TEXT,
  position INTEGER,
  FOREIGN KEY(username) REFERENCES bet_user(username)
);

-- Table containing the final bet per player
CREATE TABLE final_bet (
  id SERIAL PRIMARY KEY,
  username TEXT,
  team TEXT NOT NULL,
  bet INTEGER NOT NULL,
  result INTEGER NOT NULL,
  success INTEGER,
  FOREIGN KEY(username) REFERENCES bet_user(username)
);

-- Table containing a player's bet on a match
CREATE TABLE match_bet (
  id SERIAL PRIMARY KEY,
  username TEXT,
  match_id INTEGER NOT NULL,
  goal1 INTEGER,
  goal2 INTEGER,
  bet INTEGER,
  FOREIGN KEY(username) REFERENCES bet_user(username)
);

-- Messages which can be written on the default page by the admin
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  message TEXT
);

-- Creating default 5 messages
INSERT INTO messages (id, message) VALUES (1, '');
INSERT INTO messages (id, message) VALUES (2, '');
INSERT INTO messages (id, message) VALUES (3, '');
INSERT INTO messages (id, message) VALUES (4, '');
INSERT INTO messages (id, message) VALUES (5, '');

-- Table holding discussion comments
CREATE TABLE comment (
  id SERIAL PRIMARY KEY,
  username TEXT,
  datetime TEXT NOT NULL,
  content TEXT,
  FOREIGN KEY(username) REFERENCES bet_user(username)
);