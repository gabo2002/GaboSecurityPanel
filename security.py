
import json
from utilities import scriviFileLog


class security():

    config = json.load(open("config.json","r"))
    superUser = config['super_user']
    TOKEN = config['token']
    ids = config['allowed_ids']

    def __init__(self):
        pass

    @staticmethod
    def utenteAutorizzato(update):
        if -1 in security.ids or update.message.from_user.id in security.ids:
            return True
        if -1 in security.superUser or update.message.from_user.id in security.superUser:
            return True
        scriviFileLog("Tentativo di accesso non autorizzato da Username: {} Id: ".format(update.message.from_user.username,update.message.from_user.id))
        return False

    @staticmethod
    def isSuperUser(update):
        if update.message.from_user.id in security.superUser or -1 in security.superUser:
            return True
        scriviFileLog("Tentativo di accesso non autorizzato da Username: {} Id: ".format(update.message.from_user.username,update.message.from_user.id))
        return False
