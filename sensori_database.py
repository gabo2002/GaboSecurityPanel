import psutil
import sqlite3
import os
import time
from threading import Thread

class SensoriDatabase(Thread):
    '''
        Classe che si occupa di gestire e inserire i dati di utilizzo del server sulla quale gira
        La seguente classe e' un thread a se stante, una volta avviato non dovra' interagire con nessuno, se non con il database
    '''

    def __init__(self,nomeFile):
        self.nomeFile = nomeFile
        Thread.__init__(self)
        if not os.path.isfile(nomeFile):        #se non esiste, creo il database
            con = sqlite3.connect(nomeFile)
            cursore = con.cursor()
            cursore.execute("CREATE TABLE  cpu (id INTEGER PRIMARY KEY AUTOINCREMENT,data datetime not null default (datetime('now','localtime')) , coreid integer not null, valore double not null)")
            cursore.execute("CREATE TABLE ram (id INTEGER PRIMARY KEY AUTOINCREMENT, data datetime not null default (datetime('now','localtime')),bytes BIGINT not null)")
            cursore.execute("CREATE TABLE network (id INTEGER PRIMARY KEY AUTOINCREMENT, data datetime not null default (datetime('now','localtime')),nic varchar(20) not null,bs integer not null,br integer not null)")
            cursore.execute("CREATE TABLE swap (id INTEGER  PRIMARY KEY AUTOINCREMENT,data datetime not null default (datetime('now','localtime')),bytes BIGINT not null)")
            con.commit()
            cursore.close()
            con.close()
        print("Thread SensoriDatabase startato con successo!")    

    def run(self):
        self.con = sqlite3.connect(self.nomeFile)
        self.cursore = self.con.cursor()
        while True:
            tempo0 = time.time()
            self.__getNetworkUsage()
            self.__getRamUsege()
            self.__getCpuUsage()
            tempo1 = time.time()
            time.sleep(60 - (tempo1-tempo0))    #IN questo modo ciclo ogni 60 secondi esatti, rimuovo i tempi di esecuzione delle funzioni (utilizzano 0.5s per fare la stima della cpu usata ecc...)

    def __getNetworkUsage(self):

        intervallo = 0.5    #intervallo su cui calcolare la velocita' attuale (Isaac Newton con la sua velocita' istantanea non sarebbe contento)

        tempo0 = time.time()

        download0 = list()
        upload0 = list()
        valori = psutil.net_io_counters(pernic=True)
        
        for chiave in valori.keys():
            nic = valori[chiave]
            download0.append(nic.bytes_recv)
            upload0.append(nic.bytes_sent)

        time.sleep(intervallo)

        download1 = list()
        upload1 = list()
        valori = psutil.net_io_counters(pernic=True)
        
        for chiave in valori.keys():
            nic = valori[chiave]
            download1.append(nic.bytes_recv)
            upload1.append(nic.bytes_sent)  
        tempo1 = time.time()

        valori = list(valori.keys())
        for i in range(len(download0)):
            nic = valori[i]
            down =  round ( (download1[i]-download0[i]) / (tempo1 - tempo0) , 3)
            up =  round( (upload1[i]- upload0[i]) / (tempo1 - tempo0) ,3)
            self.cursore.execute("INSERT INTO network (nic,bs,br) VALUES (?,?,?)",[nic,up,down])

        self.con.commit()

    def __getCpuUsage(self):
        valori = psutil.cpu_percent(interval=0.5,percpu=True)
        counter = 0
        for valore in valori:
            self.cursore.execute("INSERT INTO cpu (coreid,valore) VALUES (?,?)",[counter,valore])
            counter+=1
        self.con.commit()

    def __getRamUsege(self):
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()

        self.cursore.execute("INSERT INTO ram (bytes) VALUES (?)",[ram.used])
        self.cursore.execute("INSERT INTO swap (bytes) VALUES (?)",[swap.used])
        self.con.commit()
