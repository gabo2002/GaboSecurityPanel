import subprocess 
from fcntl import fcntl,F_GETFL,F_SETFL
from os import O_NONBLOCK,read,write
import time
import os
import pyte
from telegram import ParseMode 
import threading
from security import security

from telegram.ext import ConversationHandler

oggettoComando = None
thread = None
isRunning = False


def comandoAsincrono(update,context,comando):
    ritorno = subprocess.run(comando.split(),capture_output=True)
    update.message.reply_text(ritorno.stdout.decode("UTF-8"))
    

def terminaComando():
    global oggettoComando,thread,isRunning

    isRunning = False
    thread = None
    oggettoComando = None
    return ConversationHandler.END


def checkFine():
    global thread
    while True:
        try:
            thread.join(0.1)
            if not thread.is_alive():
                terminaComando()
                return
        except Exception as e:
            terminaComando()
            return

def scriviSuProx(update,context):
    global oggettoComando,thread,isRunning
    testo = update.message.text
    if oggettoComando is None:

        try:
            comandi = update.message.text.split("/command")[1]
            return comando(update,context)
        except Exception as e:
            pass

        return terminaComando()
        

    oggettoComando.scriviSuBuffer(testo)
    thread.join(0.5)

    if thread.is_alive():
        return 1
    else: 
        return terminaComando()

def comando(update,context):
    if not security.utenteAutorizzato(update):
        return 

    global oggettoComando
    global thread 
    global isRunning

    stdin = None
    comandi = update.message.text.split("/command",1)[1]
    
    oggettoComando = Comando("")

    thread = threading.Thread(target=oggettoComando.eseguiComando,args=(comandi,update,context,stdin))
    thread.start()
    isRunning = True

    thread.join(1)

    if thread.is_alive():
        threading.Thread(target=checkFine).start()
        return 1
    else: 
        return terminaComando()

class Comando():

    def __init__(self,buffer):
        super().__init__()
        self.buffer = buffer

    def scriviSuBuffer(self,testo):
        self.buffer = testo + "\n"

    def eseguiComando(self,cmd,update,context,stdinFake):
        screen = pyte.Screen(80,24)
        stream =  pyte.Stream(screen)
        try:
            r,w = os.pipe()
            inputData = os.fdopen(w,"w")
            outputData = os.fdopen(r,"r")
            processo = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stdin=outputData)      #processo 
            
            flags = fcntl(processo.stdout, F_GETFL) # prendi i flag dell'stdout attualmente presenti
            fcntl(processo.stdout, F_SETFL, flags | O_NONBLOCK) #ci aggiunto il non bloccante

            check = True

            flags = fcntl(outputData, F_GETFL) # prendi i flag dell'stdin attualmente presenti
            fcntl(outputData, F_SETFL, flags | O_NONBLOCK) #ci aggiunto il non bloccante

            while True:
                time.sleep(0.5)
                try:
                    stringa = read(processo.stdout.fileno(),8192).decode("utf-8")   #leggo (ogni 0.5s) l'stdout del processo
                    stringa = stringa.replace("\n","\r\n").replace("\r\r\n","\r\n") # sostituisco i \n con \r\n, se gia' presenti il secondo replace fixa tutto
                    stream.feed(stringa)  #il mio terminale riceve in pasto la stringa da elaborare 

                    if stringa == "":   #non ho letto nulla, potrebbero esserci dei problemi
                        context.bot.send_message(update.message.chat_id,"Il comando non ha prodotto alcun output, sicuro di averlo digitato correttamente?")
                        return

                    stringaTott = ""
                    for riga in screen.display:     #screen.display: array di stringhe, ogni riga rappresenta una riga del terminale
                        stringaTott += riga

                    stringaTott = "\n".join(stringaTott[i:i+80] for i in range(0,len(stringaTott),80))
                    
                    html = os.popen('printf "'+stringaTott.replace("%","%%")+'" | aha --black --line-fix').read()
                    html = "".join(html.split("\n")[i]+"\n" for i in range(9,len(html.split("\n")[:-3])))       #rimuove le prime 9 linee e le ultime 3, (contengono header html che non piacciono a telegram)


                    if html.replace(" ","").replace("\n","") == "<pre></pre>":      #brutale, controllo se il contenuto e' vuoto
                        html = "Loading"

                    if check:       #primo messaggio
                        ritorno = update.message.reply_text(html,parse_mode=ParseMode.HTML)
                        check = False
                        oldHtml = html
                        oldBuffer = self.buffer + ""
                        inputData.write(self.buffer)
                        inputData.flush()
                             
                    elif oldHtml != html:   #dal secondo messaggio in poi
                        context.bot.edit_message_text(chat_id=ritorno.chat.id,message_id=ritorno.message_id,text=html,parse_mode=ParseMode.HTML)
                        oldHtml = html

                    if self.buffer != oldBuffer:
                        inputData.write(self.buffer)
                        inputData.flush()
                        oldBuffer = self.buffer + ""
                    #Decommentare questa linea per il debug
                    #os.system(' printf  "'+stringaTott.replace("%","%%")+'" | aha --black --line-fix  > prova.html')
                    if processo.poll() is not None:
                        break
                except OSError as e:
                    pass

            status = processo.returncode
        except subprocess.CalledProcessError as obj:
            status = obj.returncode
        return status
