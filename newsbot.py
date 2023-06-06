from time import sleep
from origamibot import OrigamiBot as Bot
from origamibot.listener import Listener

import sqlite3
import datetime
import json

with sqlite3.connect("DFP.db") as con:
    c = con.cursor()
    ##Delete these lines when debugging gets easier
    # status_code 0 will mean unpublished and 1 will mean published
    c.execute('''CREATE TABLE IF NOT EXISTS news(date TEXT, 
                    journalist_id INT REFERENCES journalist, 
                    story TEXT, language TEXT, status_code INT)''')
    # update_condition is 1 if the journalist is in the process of formatting a story and 0 if they are not
    c.execute('''CREATE TABLE IF NOT EXISTS journalist(id INT PRIMARY KEY, name TEXT, update_condition INT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS editor(id INT PRIMARY KEY, name text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriber(id INT PRIMARY KEY, language TEXT)''')
    for table in c.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
        print("Table", table[0])
    c.close()


class BotsCommands:
    def __init__(self, bot: Bot):  # Can initialize however you like
        self.bot = bot

    def start(self, message):   # /start command
        self.bot.send_message(
            message.chat.id,
            'Hello user!\nThis is an example bot.')

        



class MessageListener(Listener):  # Event listener must inherit Listener
    def __init__(self, bot):
        self.bot = bot
        self.m_count = 0


    def my_echo(self, message):
        value = message.text.replace('/echo ','')
        self.bot.send_message(message.chat.id, value)

    def on_message(self, message):   # called on every message
        self.m_count += 1
        print("\n\n",message,"\n\n")
        with sqlite3.connect("DFP.db") as con:
            c = con.cursor()
            c.execute("SELECT * FROM journalist")
            journalists = c.fetchall()
            journalist_active = []
            journalist_inactive = []
            for journalist in journalists:
                if journalist[2] == 0:
                    journalist_inactive.append(journalist[0])
                elif journalist[2] == 1:
                    journalist_active.append(journalist[0])
            print("journalist_active")
            print(journalist_active)
            print("journalist_inactive")
            print(journalist_inactive)
                


            command = "SELECT id FROM subscriber WHERE language == '" + message.from_user.language_code + "'"
            unpublished_tuple = c.execute(command)

            if '/add_journalist' in message.text:
                try:
                    command = "INSERT INTO journalist VALUES (" + str(message.from_user.id) + ", '" + message.from_user.username + "', 0)"
                    print(command)
                    c.execute(command)
                except:
                    self.bot.send_message(message.from_user.id, "You have already been added to the journalist database")

            if '/echo' in message.text:
                self.my_echo(message)

            if '/publish' in message.text and message.from_user.id in journalist_active:
                c.execute("UPDATE journalist SET update_condition = 0")
                print('removed user')
                command = "SELECT story FROM news WHERE journalist_id == " + str(message.from_user.id) + " AND status_code = 0"
                print(command)
                c.execute(command)
                latest = c.fetchone()
                print(latest[0])
                subscribers = c.execute("SELECT id FROM subscriber WHERE language == '" + message.from_user.language_code + "'")
                for id in subscribers:
                    self.bot.send_message(id[0], latest[0])
                self.bot.send_message(message.from_user.id, "Story has been published.")

            if '/publish' not in message.text and message.from_user.id in journalist_active:               
                self.bot.send_message(message.from_user.id, message.text)
                self.bot.send_message(message.from_user.id, 'Is this what you would like to broadcast? Reply /publish if yes or send a new message if no.')
                command = "DELETE FROM news WHERE journalist_id == " + str(message.from_user.id) + " AND status_code == 0"
                print(command)
                c.execute(command)
                command = "INSERT INTO news VALUES ('" + str(datetime.date.today()) + "', " + str(message.from_user.id) + ", '" + message.text + "', '" + message.from_user.language_code + "', 0)"
                print(command)
                c.execute(command)

            if '/draft' in message.text and message.from_user.id in journalist_inactive:
                self.bot.send_message(message.from_user.id, 'Send the message you would like broadcast. I will send it back to you as it will be broadcast for final approval.')
                command = "UPDATE journalist SET update_condition = 1 WHERE id == " + str(message.from_user.id)
                print(command)
                con.execute(command)

            if '/enroll' in message.text.lower():
                command = "INSERT INTO subscriber VALUES (" + str(message.from_user.id) + ",  '" + str(message.from_user.language_code) + "')"
                print(command)
                con.execute(command)
                self.bot.send_message(message.from_user.id, 'You have been added. Thank you for being an important part of Dallas Free Press!')

                if message.from_user.language_code != 'en':
                    self.bot.send_message([[[add admin telegram id here]]], "A user has enrolled with language code " + str(message.from_user.language_code))

            if '/unenroll' in message.text.lower():
                command = "SELECT id FROM subscriber WHERE id ==" + str(message.from_user.id)
                c.execute(command)
                subscribe_true = c.fetchone()
                print(subscribe_true)
                print(message.from_user.id)
                try:
                    var = message.from_user.id in subscribe_true
                except:
                    var = False

                if var == True:
                    command = "DELETE FROM subscriber WHERE id ==" + str(message.from_user.id)
                    c.execute(command)
                    self.bot.send_message(message.from_user.id, "You have been unenrolled from the Dallas Free Press messaging list. Simply type /enroll to opt back in!")
                else:
                    self.bot.send_message(message.from_user.id, 'We could not find you in the Dallas Free Press database. Type /enroll if you are looking to opt in!')

            if '/latest_news' in message.text.lower():
                self.bot.send_message(message.from_user.id, 'Right now this is a placeholder command, when finished this command will send all the news articles that were published in the last week.')
                self.bot.send_message(message.from_user.id, 'In the meantime, check out https://dallasfreepress.com/')
            
            c.close()

    def on_command_failure(self, message, err=None):  # When command fails
        if err is None:
            self.bot.send_message(message.chat.id,
                                  'Command failed to bind arguments!')
        else:
            self.bot.send_message(message.chat.id,
                                  'Error in command:\n{err}')


if __name__ == '__main__':
    f = open('config.json')
    config = json.load(f)
    token = config['keys']['TelegramKey']
    bot = Bot(token)   # Create instance of OrigamiBot class


    # Add an event listener
    bot.add_listener(MessageListener(bot))

    # Add a command holder
    bot.add_commands(BotsCommands(bot))

    # We can add as many command holders
    # and event listeners as we like

    bot.start()   # start bot's threads
    while True:
        sleep(1)
        # Can also do some useful work i main thread
        # Like autoposting to channels for example

