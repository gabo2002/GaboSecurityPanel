


import subprocess
import sys
import io
from fcntl import fcntl,F_GETFL,F_SETFL
from os import O_NONBLOCK,read
import time
import os

import re

def getStringhe(testo):

    testo = repr(testo)     #magia
    modifiche = []

    #print(re.compile("/.+?(?=\\x1b\[[0-9]+;[0-9]+H[a-zA-Z]+)/").split(testo))
    valori = testo.split("\\x1b[")

    for valore in valori:
        if valore == "":
            continue

        subString = valore.split(";",1)      

        try:
            posx = int(subString[0])

            if subString[1][2] == "H":
                posy = int(subString[1][:2])
            elif subString[1][1] == "H":
                posy = int(subString[1][:1])
            else:
                raise ArithmeticError("Non esiste")
        except Exception as e:
            continue
        
        payload = valore[2+len(str(posx))+len(str(posy)):]
        
        #print("valori trovati: {} e {}, payload: {}".format(posx,posy,payload))
        modifiche.append((posx,posy,payload))
    return modifiche


buffer  = []





def runGAbo(cmd):

    try:

        args = cmd.split(cmd)
        #status = subprocess.call(cmd, shell=True,stdout=subprocess.PIPE,stdin=sys.stdin)
        processo = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stdin=sys.stdin)
        flags = fcntl(processo.stdout, F_GETFL) # get current p.stdout flags
        fcntl(processo.stdout, F_SETFL, flags | O_NONBLOCK)
        stringaTot = ""
        while True:
            time.sleep(0.1)
            try:
                stringa = read(processo.stdout.fileno(),8192).decode("utf-8")
                #print(stringa)
                
                file = open("test.txt","a")
                file.write(str(getStringhe(stringa))+"\n")
                file.close()
                
                
                file = open("output.txt","a")
                file.write(stringa)
                file.close()


                stringaTot += stringa
                os.system('printf "'+stringaTot.replace("%","%%")+'" | aha --black --line-fix  > prova.html')
                if processo.poll() is not None:
                    break
                #outputMemory.write(processo.stdout.read())
            except OSError:
                pass

        
        status = processo.returncode
    except subprocess.CalledProcessError as obj:
        status = obj.returncode
    return status



