import datetime
import os
if not os.path.isdir("../logs"):
    os.mkdir("../logs")
class log:
    def log(self, mensaje, archivo,printed=False):
        now = datetime.datetime.now()
        file = open("../" + archivo, "a")
        ahora=str(now)
        file.write(ahora + ": " + str(mensaje) + "\n\n")
        if printed:
            print(ahora + ": " + str(mensaje) + "\n\n")
        file.close()
