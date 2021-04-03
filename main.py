import psutil
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler,ConversationHandler,MessageHandler,Filters

from threadStart import checker
import os
from utenti import getUtentiConnessi
from security import security
from grafici import Grafico
from utilities import scriviFileLog
from comando import *
from datetime import timedelta
import sensori_database 

check = None
graficoOggetto = Grafico("botTelegram.db")

def kill(update,context):
    '''
        Questa funzione, se invocata, dopo i dovuti controlli, uccide il processo desiderato

        :param update: Oggetto di tipo Update invocato dalla chiamata del comando /kill
        :param context: Oggetto di tipo Context invocato dalla chiamata del comando /kill
        :type update: telegram.Update
        :type context: telegram.Context
        :return: None
        :rtype: None
    '''
    if not security.isSuperUser(update): #solo i superUser possono killare un processo
        context.bot.send_message(update.message.chat_id,"Non sei un superAdmin")
        return

    try:
        pid = int(update.message.text.split()[1])   
        if os.getpid() == pid:          #sto provando a killare il bot
            context.bot.send_message(update.message.chat_id,"Errore! Non puoi killare il bot telegram!")
            scriviFileLog("Quel simpaticone di {} {} ha cercato di killare il bot telegram".format(update.message.from_user.username,update.message.from_user.id))
            return
        processo = psutil.Process(pid)
        processo.terminate() 
    except psutil.AccessDenied as e:    #lo script non gira come root
        context.bot.send_message(update.message.chat_id,"Errore! Impossibile killare il processo con pid: "+str(pid))
        scriviFileLog("L'utente Username: {} Id: {} ha prova a killare il processo: ".format(update.message.from_user.username,update.message.from_user.id)+str(pid))
        return
    except psutil.NoSuchProcess as e:   #non esiste un processo con quel pid
        context.bot.send_message(update.message.chat_id,"Errore! Il processo con pid {} non esiste!".format(pid))
        return
    except IndexError as e: #eccezione sollevata con .split(): non ho messo nulla dopo /kill
        context.bot.send_message(update.message.chat_id,"Errore! utilizzo: /kill <pid>")
        return
    except ValueError as e: #Conversione a numero intero fallita: qualcuno ha messo delle lettere o simboli
        context.bot.send_message(update.message.chat_id,"Errore! Pid number non valido")
        return
    context.bot.send_message(update.message.chat_id,"Processo con pid {} killato con successo".format(pid))
    scriviFileLog("L'utente Username: {} Id: {} ha killato il processo: ".format(update.message.from_user.username,update.message.from_user.id)+str(pid))

def start(update,context):
    global check
    if not security.utenteAutorizzato(update):
        scriviFileLog("Tentativo da: "+str(update.message.from_user))
        return
    if check is None:
        check = checker(context)
        check.addUser(update.message.from_user.id)
        check.start()
    else:
        check.addUser(update.message.from_user.id)

    scriviFileLog("L'utente autorizzato Username: {} Id: {} ha avviato il bot".format(update.message.from_user.username,update.message.from_user.id))
    #da rimuovere
    context.bot.send_message(update.message.from_user.id,"Ciao, sei autorizzato a usare questo BOT!, da adesso in poi riceverai una notifica ogni qualvolta si connettera' un nuovo utente")

def notifica(update,context):
    '''
        Funzione che, se invocata, invia il testo seguito dopo /notifica a tutti i membri autorizzati che abbiano avviato il Bot

        :param update: Oggetto di tipo Update invocato dalla chiamata del comando /kill
        :param context: Oggetto di tipo Context invocato dalla chiamata del comando /kill
        :type update: telegram.Update
        :type context: telegram.Context
        :return: None
        :rtype: None
    '''
    if not security.utenteAutorizzato(update):
        context.bot.send_message("Attenzione! Non hai i permessi per utilizzare il comando /notifica")
        return
    testo = "Utilizzo: /notifica <testo>"
    try:
        testo = update.message.text.split("/notifica")[1]   #ottengo il testo
    except Exception as e:  #viene inviato 
        context.bot.send_message(update.message.chat_id,"Utilizzo: /notifica <testo>")
        return

    utenti = check.getUsers()

    if len(utenti) == 1:     #ci sono solo io
        context.bot.send_message(update.message.chat_id,"Sei l'unico admin, non posso inviare la notifica a nessuno")

    for utente in utenti:       #Invio testo ad ogni utente
        if utente != update.message.from_user.id:
            context.bot.send_message(utente,testo)

def errore_inaspettato(update,context):
    context.bot.send_message(update.message.chat_id,"Ho riportato un'eccezione inaspettata! Per cortesia contattare l'amministratore del server!")
    scriviFileLog("Abbiamo riscontrato un errore inaspettato: testo del comando: {}, username persona: {}, id persona {}, errore: {}".format(update.message.text,update.message.from_user.username,update.message.from_user.id,context.error))
    print("Errore inaspettato: {}".format(context.error))

def grafico(update,context):
    if not security.utenteAutorizzato(update):
        return
    keyboard = [
        [InlineKeyboardButton("Network", callback_data='NETWORK'),InlineKeyboardButton("RAM", callback_data='RAM')],
        [InlineKeyboardButton("CPU", callback_data='CPU'),InlineKeyboardButton("SWAP",callback_data="SWAP")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Quale dei seguenti grafici vuoi visualizzare:', reply_markup=reply_markup)
    print("Hai scelto: ")
    return 1

def ottieniArco(update,context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Mese", callback_data=query.data+'-mese'),InlineKeyboardButton("Giorno", callback_data=query.data+'-giorno')],
        [InlineKeyboardButton("Ora", callback_data=query.data+'-ora')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text='Quando visualizzare il grafico:', reply_markup=reply_markup)
    return 2

def ottieniGrafico(update,context):
    query = update.callback_query
    query.answer()
    global graficoOggetto
    
    messaggio = query.data
    query.edit_message_text(text="Invio grafico "+messaggio.split("-")[0])

    dataEnd = datetime.now()
    stringaDataEnd = dataEnd.strftime("'%Y-%m-%d %H:%M:%S")


    if "ora" in messaggio:
        dataStart = dataEnd - timedelta(minutes=60)
        stringaDataStart = dataStart.strftime('%Y-%m-%d %H:%M:%S')
    elif "giorno" in messaggio:
        dataStart = dataEnd - timedelta(hours=24)
        stringaDataStart = dataStart.strftime('%Y-%m-%d %H:%M:%S')
    elif "mese" in messaggio:
        dataStart = dataEnd - timedelta(days=30)
        stringaDataStart = dataStart.strftime('%Y-%m-%d %H:%M:%S')

    if "RAM" in messaggio:
        context.bot.send_photo(query.message.chat.id,photo=graficoOggetto.getGraficoRam(dataStart,dataEnd))
    elif "SWAP" in messaggio:
        context.bot.send_photo(query.message.chat.id,photo=graficoOggetto.getGraficoRam(dataStart,dataEnd,swap=True))
    elif "CPU" in messaggio:
        if messaggio.split("-")[2] == "a":
            context.bot.send_photo(query.message.chat_id,photo=graficoOggetto.getGraficoCpu(dataStart,dataEnd))
        else:
            context.bot.send_photo(query.message.chat_id,photo=graficoOggetto.getGraficoCpu(dataStart,dataEnd,idCpu=int(messaggio.split("-")[2]))) 
    elif "NETWORK" in messaggio:
        if messaggio.split("-")[2] == "a":
            context.bot.send_photo(query.message.chat_id,photo=graficoOggetto.getGraficoNetwork(dataStart,dataEnd))
        else:
            context.bot.send_photo(query.message.chat_id,photo=graficoOggetto.getGraficoNetwork(dataStart,dataEnd,nomeNic=messaggio.split("-")[2]))


def cpuCore(update,context):

    core = psutil.cpu_count(logical=True)
    query = update.callback_query
    query.answer()

    keyboard = []
    riga = []
    for i in range(2):  #2 righe
        for j in range(int(core)//2):
            riga.append(InlineKeyboardButton(str(j+(i*core//2)),callback_data=query.data+"-"+str(j*(i+1))))
        keyboard.append(riga.copy())
        riga = []

    riga = [InlineKeyboardButton("Media generale",callback_data=query.data+"-a")]
    keyboard.append(riga)

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text='Selezionare quale core visualizzare:', reply_markup=reply_markup)
    return 3

def network(update,context):
    query = update.callback_query
    query.answer()
    
    nics = graficoOggetto.getSchedeDiRete()
    keyboard = []
    riga = []

    for i in range(2):  #2 righe
        for j in range(len(nics)//2):
            riga.append(InlineKeyboardButton(nics[j+(i*len(nics)//2)],callback_data=query.data+"-"+nics[j+(i*len(nics)//2)]))
        keyboard.append(riga.copy())
        riga = []

    riga = [InlineKeyboardButton("Tutte le interfacce",callback_data=query.data+"-a")]
    keyboard.append(riga)

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text='Selezionare quale Nic visualizzare', reply_markup=reply_markup)
    return 3


def schedule(update,context):

    if not security.utenteAutorizzato(update):
        context.bot.send_message(update.message.chat_id,"Non sei autorizzato a utilizzare questo comando!")
        return
    
    testo = update.message.text
    testo = testo.replace("/schedule ","")
    split = testo.split(" ",1)

    data = split[0]
    comando_str = split[1]
    
    timeNow = datetime.now()

    orario = datetime.strptime(data,"%Y/%m/%d-%H:%M:%S")

    secondi = (orario - timeNow).total_seconds()

    if secondi >= 0:
        threading.Timer(secondi, comandoAsincrono,args=(update,context,comando_str)).start()
        context.bot.send_message(update.message.chat_id,"Il tuo comando verra' eseguito all' ora specificata")
    else:
        context.bot.send_message(update.message.chat_id,"Errore! Hai inserito una data gia' passata")

def help(update,context):

    stringa = open("help.txt").read()
    
    update.message.reply_text(stringa)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('grafico', grafico)],
    states={
        1: [
            CallbackQueryHandler(ottieniArco),
        ],
        2: [
            CallbackQueryHandler(ottieniGrafico,pattern="^RAM.*"),
            CallbackQueryHandler(ottieniGrafico,pattern="^SWAP.*"),
            CallbackQueryHandler(cpuCore, pattern='^CPU.*'),
            CallbackQueryHandler(network,pattern="^NETWORK.*"),
        ],
        3: [
            CallbackQueryHandler(ottieniGrafico,pattern="^CPU.*"),
            CallbackQueryHandler(ottieniGrafico,pattern="^NETWORK.*"),
        ],
    },
    fallbacks=[CommandHandler('grafico', grafico)],
)

conv_handler_comando = ConversationHandler(

    entry_points=[CommandHandler("command",comando)],

    states={
        1: [
            MessageHandler(Filters.all,scriviSuProx)
        ],
    },
    fallbacks=[CommandHandler("help",None)],
)

gestore  = sensori_database.SensoriDatabase("botTelegram.db")
gestore.start()
updater = Updater(security.TOKEN,use_context=True)
disp = updater.dispatcher
disp.add_handler(CommandHandler("utenti",getUtentiConnessi))
disp.add_handler(CommandHandler("start",start))
disp.add_handler(CommandHandler("kill",kill))
disp.add_handler(CommandHandler("schedule",schedule))
disp.add_handler(CommandHandler("notifica",notifica))
disp.add_handler(CommandHandler("help",help))
disp.add_handler(conv_handler_comando)
disp.add_error_handler(errore_inaspettato)


disp.add_handler(conv_handler)

updater.start_polling()


updater.idle()