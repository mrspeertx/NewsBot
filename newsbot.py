from time import sleep
from origamibot import OrigamiBot as Bot
from origamibot.listener import Listener

import sqlite3
import datetime
import json

with sqlite3.connect("DFP.db") as con:
    c = con.cursor()
    ##Delete these lines when debugging gets easier
    # update_condition is 1 if the journalist is in the process of formatting a story and 0 if they are not
    c.execute('''CREATE TABLE IF NOT EXISTS journalist(id INT PRIMARY KEY, name TEXT, update_condition INT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS editor(id INT PRIMARY KEY, name text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriber(id INT PRIMARY KEY, language TEXT)''')
    # status_code 0 will mean unpublished and 1 will mean published
    c.execute('''CREATE TABLE IF NOT EXISTS news(date TEXT, 
                    journalist_id INT REFERENCES journalist, 
                    story TEXT, language TEXT, status_code INT)''')
    for table in c.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
        print("Table", table[0])
    c.close()


class BotsCommands:
    def __init__(self, bot: Bot):  # Can initialize however you like
        self.bot = bot

    def start(self, message):   # /start command
         with sqlite3.connect("DFP.db") as con:
            c = con.cursor()
            command = "INSERT INTO subscriber VALUES(:id, :language)"
            data = {"id": message.from_user.id, "language" : message.from_user.language_code}
            try:
                con.execute(command, data)
                self.bot.send_message(message.from_user.id, 'You have been added to the Dallas Free Press messaging list. Thank you for being an important part of independent local journalism!')
            except:
                self.bot.send_message(message.from_user.id, "It looks like you have already enrolled.")

        



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
                

            data = {"language": message.from_user.language_code}
            command = "SELECT id FROM subscriber WHERE language == (:language)"
            unpublished_tuple = c.execute(command,data)

            if '/add_journalist' in message.text:
                try:
                    command = "INSERT INTO journalist VALUES(:id, :username, :update_condition)"
                    data = {"id": message.from_user.id, "username": message.from_user.username, "update_condition": 0}
                    c.execute(command, data)                                                            
                except:
                    self.bot.send_message(message.from_user.id, "You have already been added to the journalist database")

            if '/echo' in message.text:
                self.my_echo(message)

            if '/publish' in message.text and message.from_user.id in journalist_active:
                c.execute("UPDATE journalist SET update_condition = 0")
                print('removed user from active journalist')
                data = {"id": message.from_user.id, "status_code": 0}
                command = "SELECT story FROM news WHERE journalist_id == (:id) AND status_code = (:status_code)"
                c.execute(command,data)
                latest = c.fetchone()
                print(latest[0])
                command = "SELECT id FROM subscriber WHERE language == (:language_code)"
                data = {"language_code": message.from_user.language_code}
                subscribers = c.execute(command, data)
                for id in subscribers:
                    self.bot.send_message(id[0], latest[0])
                self.bot.send_message(message.from_user.id, "Story has been published.")

            if '/publish' not in message.text and message.from_user.id in journalist_active:               
                self.bot.send_message(message.from_user.id, message.text)
                self.bot.send_message(message.from_user.id, 'Is this what you would like to broadcast? Reply /publish if yes or send a new message if no.')
                command = "DELETE FROM news WHERE journalist_id == (:id) AND status_code == (:status_code)"
                data = {"id": message.from_user.id, "status_code": 0}
                c.execute(command,data)
                command = "INSERT INTO news VALUES(:date, :id, :message, :language, :status_code)"
                data = {"date": str(datetime.date.today()), 
                        "id": message.from_user.id, 
                        "message": message.text, 
                        "language": message.from_user.language_code,
                        "status_code": 0}                 
                c.execute(command, data)

            if '/draft' in message.text and message.from_user.id in journalist_inactive:
                self.bot.send_message(message.from_user.id, 'Send the message you would like broadcast. I will send it back to you as it will be broadcast for final approval.')
                command = "UPDATE journalist SET update_condition = (:update_condition) WHERE id == (:id)"
                data = {"update_condition": 1, "id": message.from_user.id}
                con.execute(command,data)

            if '/enroll' in message.text.lower():
                command = "INSERT INTO subscriber VALUES(:id, :language)"
                data = {"id": message.from_user.id, "language": message.from_user.language_code}
                try:
                    con.execute(command, data)
                    self.bot.send_message(message.from_user.id, 'You have been added. Thank you for being an important part of Dallas Free Press!')
                except:
                    self.bot.send_message(message.from_user.id, "It looks like you have already enrolled.")

                if message.from_user.language_code != 'en':
                    f = open('config.json')
                    config = json.load(f)
                    admin_id = config['admin_id']
                    self.bot.send_message(admin_id, "A user has enrolled with language code " + str(message.from_user.language_code))

            if '/unenroll' in message.text.lower():
                command = "SELECT id FROM subscriber WHERE id == (:id)"
                data = {"id": message.from_user.id}
                c.execute(command,data)
                subscribe_true = c.fetchone()
                print(subscribe_true)
                print(message.from_user.id)
                try:
                    var = message.from_user.id in subscribe_true
                except:
                    var = False

                if var == True:
                    command = "DELETE FROM subscriber WHERE id == (:id)"
                    data = {"id": message.from_user.id}
                    c.execute(command,data)
                    self.bot.send_message(message.from_user.id, "You have been unenrolled from the Dallas Free Press messaging list. \nSimply type /enroll to opt back in!")
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

