#------------
# Importante
#------------
# Este deleter parte de las siguientes bases:
#   El deleter se corre inmediatamente despues de cargar una partida erronea
#   Luego de borrar la partida erronea, la version correcta se va a subir

import sqlalchemy as db
import time
import trueskill
from datetime import date

#--------------------------------
# Conectar a SQL, definir tablas
#--------------------------------
engine = db.create_engine("oracle://system:smash@127.0.0.1:1521/smash")
conn = engine.connect() 
metadata = db.MetaData() #extracting the metadata
player = db.Table('player', metadata, autoload=True, autoload_with=engine)
deck = db.Table('deck', metadata, autoload=True, autoload_with=engine)
match = db.Table('match', metadata, autoload=True, autoload_with=engine)

# Agarrar el ultimo partido
query = conn.execute("select max(match_number) from match where match_date = '"+date.today().strftime("%d-%b-%Y")+"'")
match_number = query.fetchall()[0][0]

# Agarrar players y decks
players = []
decks = []

query = conn.execute("select * from match where match_date = '"+date.today().strftime("%d-%b-%Y")+"' and match_number = "+str(match_number))
match_data = query.fetchall()

for found in range(0,4):
    players.append(match_data[found][2])
    decks.append(match_data[found][3])

print()
print("-------------------")
print("Datos de la partida")
print("-------------------")
print("Fecha: "+date.today().strftime("%d-%b-%Y")+", partida numero "+str(match_number))
print("Ganador: "+players[0]+" ("+decks[0]+")")
print("Mesa: "+players[1]+" ("+decks[1]+"), "+players[2]+" ("+decks[2]+"), "+players[3]+" ("+decks[3]+")")
borrar = input("Desea borrar la partida? (Y/N): ")

#-------------------
# Borrar la partida
#-------------------

if borrar == "Y":
    for player in range(0,4):
        query = conn.execute("delete from player where name = '"+players[player]+"' and newest = 'Y'")
        query = conn.execute("update player set newest = 'Y' where newest = 'P' and name = '"+players[player]+"'")
    for deck in range(0,4):
        query = conn.execute("delete from deck where name = '"+decks[deck]+"' and newest = 'Y'")
        query = conn.execute("update deck set newest = 'Y' where newest = 'P' and name = '"+decks[deck]+"'")
    query = conn.execute("delete from match where match_date = '"+date.today().strftime("%d-%b-%Y")+"' and match_number = "+str(match_number))    
else:
    print("Abortando")
    quit()