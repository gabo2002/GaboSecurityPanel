import urllib3
import flag
import psutil
import json
import prettytable
from datetime import datetime
from utilities import scriviFileLog
from security import *
from telegram import ParseMode  


def getUtentiConnessi(update,context):
    '''
        Questa funzione, se invocata, dopo i dovuti controlli, mostra gli utenti attualmente connessi.

        L'utente che invoca il comando /utenti ricevera' una tabella contenenti ogni utente connesso.
        Nella tabella verranno riportati Username, Indirizzo IP (o terminale) dalla quale e' collegato, con relativa bandiera indicante la nazione dalla quale e' connesso, Data e ora di login e il relativo PID.

        :param update: Oggetto di tipo Update invocato dalla chiamata del comando /utenti
        :param context: Oggetto di tipo Context invocato dalla chiamata del comando /utenti
        :type update: telegram.Update
        :type context: telegram.Context
        :return: None
        :rtype: None
    '''

    if not security.utenteAutorizzato(update):   #non sono un utente autorizzato dal file config.json
        return

    utenti = psutil.users()
    table = prettytable.PrettyTable()
    table.field_names = ["Campo","Valore"]

    for utente in utenti:
        table.add_row(["Nome:",utente.name])
        table.add_row(["IP:",str(utente.host) + " " + getEmoji(utente)])
        table.add_row(["Time:",parsaData(utente)])
        table.add_row(["Pid: ",utente.pid])
        table.add_row(["----","----------"])

    context.bot.send_message(update.message.chat_id,"<pre>"+str(table)+"</pre>",parse_mode=ParseMode.HTML)  #utilizzo il tag HTML <pre> per non modificare la formattazione
    scriviFileLog("Utente {} ha richiesto gli utenti connessi al server".format(update.message.from_user.id))

def getEmoji(utente):
    '''
        Funzione di supporto a getUtentiConnessi(): essa, dato un utente, ritorna l'emoji unicode corrispondente alla nazione dalla quale proviene la connessione.
        In caso di collegamenti fisici/terminali virtuali verra' riportata la nazione del server in questione

        :param utente: Oggetto di Tipo User della classe psutil
        :type utente: psutil._common.suser
        :return: Emoji della nazione dalla quale proviene la connessione
        :rtype: str
    '''
    http = urllib3.PoolManager()
    url = "http://ipinfo.io/"+utente.host+"/json"   #api rest che, dato l'indirizzo IP, ritorna informazioni geografiche 
    req = http.request("GET",url)
    if req.status == 200:
        valori = json.loads(req.data.decode("utf-8"))
        if "country" in valori.keys():
            return flag.flag(valori['country'])
        else:
            return getEmojiMacchinaLocale()
    else:   #ritorno la bandiera del mio stato
        return getEmojiMacchinaLocale()

def getEmojiMacchinaLocale():
    '''
        Funzione che, come getEmoji, ritorna l'emoji unicode corrispondente alla nazione dove e' tenuta la macchina
        :return:  Emoji della nazione dove e' dislocata la macchina
        :rtype: str
    '''
    http = urllib3.PoolManager()
    url = "http://ipinfo.io/json"
    req = http.request("GET",url)
    valori = json.loads(req.data.decode("utf-8"))
    return flag.flag(valori['country'])

def parsaData(utente):
    '''
        Funzione che formatta la data di inizio sessione di un utente nel formato "%d %month %h:%m:%s"

        :param utente: Oggetto di Tipo User della classe psutil
        :type utente: psutil._common.suser
        :return: Stringa con la data ben formattata
        :rtype: str
    '''
    date = datetime.utcfromtimestamp(int(utente.started))
    return str(date.day) +  " " + date.strftime("%B")+ " " + date.strftime("%H:%M:%S")