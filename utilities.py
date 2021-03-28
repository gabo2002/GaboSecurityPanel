from datetime import datetime

def scriviFileLog(text):
    file = open("BotTelegramLog.txt","a")
    file.write("Ora: "+str(datetime.now())+" Contenuto: "+text+"\n")
    file.close()