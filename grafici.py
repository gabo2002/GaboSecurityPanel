import sqlite3

import matplotlib.pyplot as plt
from datetime import datetime
import io

class Grafico():
    '''
        Questa classe, grazie all'utilizzo della libreria MatPlotLiB, fornisce i grafici, in un determinato lasso di tempo,
        attingendo ai dati dal database .sqlite

        La seguente classe e' in grado di fornire i grafici di:\n
            - CPU, divisa tra singolo core e media generale
            - RAM, in MiB
            - SWAP, in Mib
            - Network, divisa tra generale e singolo NIC
    '''

    def __init__(self,nomeFile):
        self.nomeFile = nomeFile

    def getGraficoCpu(self,dataStart,dataEnd,idCpu=-1):
        self.con = sqlite3.connect(self.nomeFile)
        self.cursore = self.con.cursor()
        plt.close() #ripulisco il buffer di matplotlib

        if idCpu == -1:     #su tutti i core -> calcolare media in ogni punto 
            sql = "select data,avg(valore) as valore FROM cpu WHERE strftime('%Y-%m-%d %H:%M:%S',data) BETWEEN ? and ? group by data"
            elementi = self.cursore.execute(sql,[dataStart,dataEnd]).fetchall()
        else:
            sql = "SELECT data,valore FROM cpu WHERE strftime('%Y-%m-%d %H:%M:%S',data) BETWEEN ? and ? AND coreid = ?"
            elementi = self.cursore.execute(sql,[dataStart,dataEnd,idCpu]).fetchall()

        date = list()
        valori = list()

        for elemento in elementi: 
            print(elemento)
            date.append(datetime.strptime(elemento[0],'%Y-%m-%d %H:%M:%S'))
            valori.append(elemento[1])

        plt.xlabel("Data")
        plt.ylabel("Utilizzo percentuale")
        plt.plot(date,valori)
        plt.gcf().autofmt_xdate()
        plt.legend(["Utilizzo (%)"])
        
        buffer = io.BytesIO()
        buffer.name = "GraficoCPU.png"
        plt.savefig(buffer,format="png")
        buffer.seek(0)
        self.cursore.close()
        self.con.close()
        return buffer

    def getGraficoRam(self,dataStart,dataEnd,swap=False):
        self.con = sqlite3.connect(self.nomeFile)
        self.cursore = self.con.cursor()
        plt.close() #ripulisco il buffer di matplotlib

        if swap:
            sql = "SELECT bytes,data FROM swap WHERE strftime('%Y-%m-%d %H:%M:%S',data) BETWEEN ? and ?"
            elementi = self.cursore.execute(sql,[dataStart,dataEnd]).fetchall()
        else:
            sql = "SELECT bytes,data FROM ram WHERE strftime('%Y-%m-%d %H:%M:%S',data) BETWEEN ? and ?"
            elementi = self.cursore.execute(sql,[dataStart,dataEnd]).fetchall()
        
        date = list()
        valori = list()

        for elemento in elementi: 
            print(elemento)
            date.append(datetime.strptime(elemento[1],'%Y-%m-%d %H:%M:%S'))
            valori.append(elemento[0]/2**20)    #da bytes a MiB

        plt.xlabel("Data")
        plt.ylabel("Utilizzo " + ("Swap" if swap else "Ram"))
        plt.plot(date,valori)
        plt.gcf().autofmt_xdate()
        plt.legend(["Utilizzo (Mib)"])

        buffer = io.BytesIO()
        buffer.name = "GraficoRAM.png"
        plt.savefig(buffer,format="png")
        buffer.seek(0)
        self.cursore.close()
        self.con.close()
        return buffer

    def getGraficoNetwork(self,dataStart,dataEnd,nomeNic="all"):
        self.con = sqlite3.connect(self.nomeFile)
        self.cursore = self.con.cursor()
        plt.close() #ripulisco il buffer di matplotlib
        
        if nomeNic == "all":
            sql = "select sum(bs) as bs,sum(br) as br,data FROM network WHERE strftime('%Y-%m-%d %H:%M:%S',data) BETWEEN ? and ? group by data"
            elementi = self.cursore.execute(sql,[dataStart,dataEnd]).fetchall()
        else: 
            sql = "SELECT bs,br,data FROM network WHERE strftime('%Y-%m-%d %H:%M:%S',data) BETWEEN ? and ? AND  nic = ?"
            elementi = self.cursore.execute(sql,[dataStart,dataEnd,nomeNic]).fetchall()

        date = list()
        valoriDown = list()
        valoriUp = list()

        for elemento in elementi:
            print(elemento)
            date.append(datetime.strptime(elemento[2],'%Y-%m-%d %H:%M:%S'))
            #ricevo valori in bytes al secondo, trasformo in bit/s 
            valoriDown.append(elemento[1]/8)
            valoriUp.append(elemento[0]/8)

        #normalizzo il grafico in base al valore max
        if max(valoriDown) >= 2**20 or max(valoriUp) >= 2**20:  #se il max e' sopra il mbps
            testo = "Velocita' (mbps)"
            esponente = 20
        elif max(valoriDown) >= 2**10 or max(valoriUp) >= 2**10:    #se il max e' sopra il kbps
            testo = "Velocita' (kbps)"
            esponente = 10
        else:
            testo = "Velocita' (b/s)"
            esponente = 0

        valoriDownPrint = [x/2**esponente for x in valoriDown]
        valoriUpPrint = [x/2**esponente for x in valoriUp]

        plt.xlabel("Data")
        plt.ylabel(testo)
        plt.plot(date,valoriDownPrint,"r")
        plt.plot(date,valoriUpPrint,"g")
        plt.gcf().autofmt_xdate()
        plt.legend(["Download","Upload"])
        
        buffer = io.BytesIO()
        buffer.name = "GraficoNETWORK.png"
        plt.savefig(buffer,format="png")
        buffer.seek(0)
        self.cursore.close()
        self.con.close()
        return buffer

    def getSchedeDiRete(self):
        self.con = sqlite3.connect(self.nomeFile)
        self.cursore = self.con.cursor()

        risultati = self.cursore.execute("SELECT DISTINCT nic FROM network").fetchall()

        self.cursore.close()
        self.con.close()
        return [nic[0] for nic in risultati]