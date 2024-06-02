# Betting Competition Web Application

![status](https://badgen.net/badge/status/finished/green) ![license](https://badgen.net/github/license/Ma-Pe-Ma/BettingApp)

![browser](https://badgen.net/badge/browser/working/green) 

## Description

This hobby project's goal is to host a simple betting competition on the web among a group of friends for big football/sports tournaments.

Earlier this game was carried out manually sending emails and editing files on a cloud service. This application was developed to automate many of the cumbersome tasks for the admin and to provide a user-friendly interface for the players where they can publish their tips.

This application's backend was implemented with the [Flask](https://flask.palletsprojects.com/en/3.0.x/) framework while the frontend part was designed with [Bootstrap](https://getbootstrap.com/).

## Demo

A statically seved demo of the application can be checked out [here](https://mapema.hu/assets/betting-competition/index.html).

## Course/rules of the competition
The logic of the game is quite simple. The players starts with a given amount of credits.

The reward for a betting is always calculated as simple as  `multiplier * bet amount`, however the multiplier varies for different kind of bets.

Obviously, at the end the player with the highest amount of credits wins the competition.

### Group bet
First, the user has to specify the results of the group stage. The reward will be recevied logically after finishing the group stage. 

The winning multiplier for a specific group betting can be determined this way:

* 0× if zero positions were guessed right
* 1.5× if one position was guessed right
* 2.5× if two positions were guessed right
* 4× if every position was guessed right

These values can be modified in the [configuration](#configuration-file) file.

### Tournament result bet
Also at the start of the game the player may bet on a team's tournament result. 

The player can choose a team and bet that the team

* becomes champion
* reaches the final
* reaches the semi-finals
* reaches the quarter-finals

For every possible betting there has to be an odd specified by the admin (namely 4×number of teams). The maximum value of betting credit is higher for this  than for the group betting or higher than the default value of match betting.

### Normal match betting
The core of the game is betting on the tournament matches. After the admin specifies the odds for the three possible outcomes (1, X, 2) for a match the users can bet on them.

The admin can change the maximum betting credit for each match. To raise the tensions of the game it is suggested to increase the maximum bet amount at the knockout stage progressively.

## Features

### Accounts
The players have to register an account to take part in the competition. The players have to specify the following parameters:
* `username`
* `email address`
* `password`
* preferences for email `reminders`.
* `invitation key`
* `language` of the site

There are two types of accounts `admin` and `generic user`. The `invitation key` determines the role of the player.

### Betting
The homepage of the site lists the future matches (with their date and odds). Each of them can be edited until the start of the match.
No other player can see the user's bet until the match has started.
<img width="50%" src="./screenshots/Home.png">

### Previous bets
After a match has started the match is moved to the 'previous bets' section. Here the players can see every player's earlier bets, their results and their credit amount at the end of the match.

<img width="50%" src="./screenshots/Previous.png">

### Standings
This section shows the current standings of the players of competition and the visualization of the history of the game's standings. (One data point means the credit amount of a player at the end of the examined match day so the credit amounts are not visualized after each match only at the end of the days).

<img width="50%" src="./screenshots/Standings.png">

### Group and tournament result bet
At this section the player can set the group and tournament result bet.

<img width="50%" src="./screenshots/Group.png">

### Discussing
There is a built-in chat plugin which can be used to discuss the tournament with markdown formatting.

<img width="50%" src="./screenshots/Discussing.png">

### Automatic updating + notifications
The users can ask for automatic reminders about matches to prevent missing out bets on them.

At the end of match days users can recieve the current standing of the game if they wish to.

The application automatically updates its result database after every match (but the update can be invoked manually too).

### Additional scopes for the admins
This section only appears for admins they have permission to do this additional tasks:

* set messages on the homepage
* send email message to every user
* modify the odds of the seperate mathces
* determine the group stages final result order (as it is not automated)
* determine if a user's tournament result bet was successful or not (as it is not automated)

## Hosting
The application (probably) can be hosted on any service which has Flask support.

### Self-hosting
First clone your app to a place where the server has read/write permissions like the intended `/var/www/` (write permission is needed for saving uploaded [initialization files](#team-description-files)).

To prevent package-collision problems it is suggested to create new a [conda](https://docs.conda.io/projects/conda/en/latest/index.html) environemnt. After cloning the project activate the new environment and install the dependencies:

    python -m pip install -r requirements.txt

After [setting up](#setting-up) you can run the application with Flask's development server with the following command:

    python -m flask run

While Flask's own server is suitable for developing the application, later it becomes a bottleneck when the app goes live. The suggested solution is to use a web server. 

<details>
  <summary>Self-hosting with Apache2</summary>
  
  This section guides you to set up the project it with [Apache2](https://httpd.apache.org/) through [mod_wsgi](https://modwsgi.readthedocs.io/en/master/) on Ubuntu.

  The first step is to install Apache2 and its developer tools.

    sudo apt install apache2 apache2-dev

The next step is to open the apache configuration file for your site (the default is /etc/apache2/sites-enabled/000-default.conf) then configure and add the following lines:

    WSGIDaemonProcess betting python-path=/path/to/miniconda3/envs/%env_name%/lib/python3.x/site-packages locale='C.UTF-8' threads=15 maximum-requests=20000
    WSGIScriptAlias / /path/to/BettingApp.wsgi
    WSGIProcessGroup betting
	WSGIApplicationGroup %{GLOBAL}

The next step is to install the mod_wsgi module for Apache2.

There are two possible solutions for this, one is to install it to the used conda environment:
  
    python -m pip install mod_wsgi
    
Which is then needeed to be installed to Apache's modules:

    mod_wsgi-express install-module

Copy and paste the LoadModule line to the config file.

The other solution is to install apache's own module:

    sudo apt-get install libapache2-mod-wsgi-py3

This method does not need further configuring. To enable or disable the module:

    sudo a2enmod/a2dismod mod_wsgi

After finishing the configuration restart apache2
    
    sudo systemctl restart apache2.service

Logs for the apache can be found here: `/var/log/apache2/`

You have to [create TLS certificate](https://www.digitalocean.com/community/tutorials/openssl-essentials-working-with-ssl-certificates-private-keys-and-csrs) (make sure it uses at least 2048-bit encryption) and [specify it to Apache](https://httpd.apache.org/docs/2.4/ssl/ssl_howto.html) if you want your connection to be secure.

Lastly the project configuration variables [have to be specifed](#setting-up).

</details>

## Setting up

### Fixture note

This project updates the result database with parsing fixtures from https://fixturedownload.com/. The app is set up to parse files which has this site's format.

If an other fixture format is needed to be parsed then the [database_manager.py](./app/database_manager.py) script have to be rewritten for it accordingly.

### Database

The app uses `SQLAlchemy` for database connection, which is a implementation-agnostic solution. However many specific tasks have to be solved differently with various SQL implementations. Therefore some raw queries only work with `SQLite` as it was chosen for the implementation as it is a very lightweight solution.

### Configuration file
Before launching the application the first time the correct values have to be specified in the [configuration file](./configuration.json).

After the configuration happened initialize the app with the following command:

    python -m flask init-db

### Team description files

The first registering admin is redirected to a page where two desciption csv files have to be uploaded.

One of them is a description about the teams, 

    teamname|groupid|top1|top2|top4|top8

The fields for this are the following:

* teamname: the key for a team it is the same as the key in the match fixtures
* groupid: the id of its group
* topX: odds for the tournament result bets

The other file contains the translations for the teams:

    teamname|en|hu|
    
The fields for this are the following:

* teamname: the same key as in the previous csv file
* the other columns hold the translations for the team names

<!--
### Email sending 

The email sending is implemented with the [Google API](https://developers.google.com/gmail/api/quickstart/python). First you have to create an account and a cloud project.

The process of setting up email sending is specified in [this source](./app/gmail_handler.py) file

To manually launch the automated reminders:

To immidiately send the standings (if it wasn't send due to some error):
    python -m flask standings-manual

To start scheduling (if app was rebooted midday)
* python -m flask checker-manual-->

### Translation

Currently only English version is available and it is planned to properly mark the translatable resource strings in the jinja templates. Then with flask-babel it will be possible to translate the pages easily.

To setup babel translations these commands need to be launched:

    pybabel extract -F babel.cfg -o .\app\resources\translations\messages.pot .
    pybabel init -i .\app\resources\translations\messages.pot -d .\app\resources\translations -l `hu`

    pybabel update -i .\app\resources\translations\messages.pot -d .\app\resources\translations
    pybabel compile -d .\app\resources\translations

## TO-DO
* make deploying and hosting an easier process + let's encript / hosting with pythonanywhere/digital ocean, containerization
* clean-up ReadMe

### Backlog
* email notification/smtp?
* session handling with Flask-login
* Add timezone selector for user
* forcing redirect to group bet before start + redirect to team data upload at very first startup for admin
