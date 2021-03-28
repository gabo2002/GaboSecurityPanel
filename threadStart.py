from threading import Thread
import time
import psutil
from telegram import ParseMode
import prettytable
from utenti import parsaData,getEmoji
from utilities import scriviFileLog


class checker(Thread):
    '''
       Questa classe notifica a tutti gli utenti autorizzati l'accesso in ssh, da terminale o simili
    '''

    def __init__(self,context):
        self.context = context
        self.admins = []
        Thread.__init__(self)
        print("Thread check nuovi utente startato con successo!")

    def addUser(self,id):
        self.admins.append(id)

    def getUsers(self):
        return self.admins

    def run(self):
        self.users = psutil.users()
        while True:
            nuoviUtenti = psutil.users()
            for utente in nuoviUtenti:
                if utente not in self.users:
                    table = prettytable.PrettyTable()
                    table.title = "Nuovo utente connesso"
                    table.field_names = ["Campo","Valore"]
                    table.add_row(["Nome:",utente.name])
                    table.add_row(["IP:",str(utente.host) + " " + getEmoji(utente)])
                    table.add_row(["Time:",parsaData(utente)])
                    table.add_row(["Pid: ",utente.pid])
                    #stringa = "Nuovo Utente: {}\nIP:  {}\nConnesso da: {}\nPid: {}\n\n".format(utente.name,utente.host,datetime.utcfromtimestamp(int(utente.started)),utente.pid)
                    
                    for account_telegram in self.admins:
                        scriviFileLog("Invio nuovo utente connesso a: "+str(account_telegram))
                        self.context.bot.send_message(account_telegram,"<pre>"+str(table)+"</pre>",parse_mode=ParseMode.HTML)
            self.users = nuoviUtenti
            time.sleep(2)
