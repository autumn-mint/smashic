import sqlalchemy as db
import time
import trueskill
from datetime import date

SIGMA_DEFAULT = 8.333
MU_DEFAULT = 25.000
RANKING_DEFAULT = 0.001
DEFAULT_NEW_DATE = "20-JAN-23"
 
#----------------------
# Funciones auxiliares
#----------------------
# Crear nuevo jugador (a utilizar cuando checkee si existe)
def insertNewPlayer(new_player_name):
    to_insert = db.insert(player).values(name=new_player_name, ranking=RANKING_DEFAULT, mu=MU_DEFAULT, sigma=SIGMA_DEFAULT, match_date=DEFAULT_NEW_DATE, match_number="0", newest="Y")
    result = conn.execute(to_insert)
    
# Crear nuevo deck (a utilizar cuando checkee si existe)
def insertNewDeck(new_deck_name):
    to_insert = db.insert(deck).values(name=new_deck_name, ranking=RANKING_DEFAULT, mu=MU_DEFAULT, sigma=SIGMA_DEFAULT, match_date=DEFAULT_NEW_DATE, match_number="0", newest="Y")
    result = conn.execute(to_insert)

#-------------
# Inicializar
#-------------
match_string = input('Ingresar string de partida: ')
match_elements = match_string.split(' | ');
p1, d1, p2, d2, p3, d3, p4, d4 = match_elements
players = [p1, p2, p3, p4]
decks = [d1, d2, d3, d4]

#--------------------------------
# Conectar a SQL, definir tablas
#--------------------------------
engine = db.create_engine("oracle://system:smash@127.0.0.1:1521/smash")
conn = engine.connect() 
metadata = db.MetaData() #extracting the metadata
player = db.Table('player', metadata, autoload=True, autoload_with=engine)
deck = db.Table('deck', metadata, autoload=True, autoload_with=engine)
match = db.Table('match', metadata, autoload=True, autoload_with=engine)

# Ver que numero de partido es hoy
query = conn.execute("select max(match_number) from match where match_date = '"+date.today().strftime("%d-%b-%Y")+"'")
match_number = query.fetchall()[0][0]
if match_number == None:
    match_number = 1
else:
    match_number = match_number + 1

#------------------
# Calculos players
#------------------
# Inicializar diccionario
d = {}

print("---------------------")
print("Descargando jugadores")
print("---------------------")

# Extraer data reciente de la base
for searched in range(0,len(players)):
    print("Descargando data del jugador "+players[searched])
    output = conn.execute("select mu,sigma from player where name = '"+players[searched]+"' and newest = 'Y'")
    rows = output.fetchall()
    if rows == []:
        agregar = input('Jugador desconocido: ' + players[searched] + '. Agregar a la base de datos? (Y/N): ')
        if agregar == 'Y':
            insertNewPlayer(players[searched])
            output = conn.execute("select mu,sigma from player where name = '"+players[searched]+"' and newest = 'Y'")
            rows = output.fetchall()
            print('Nuevo jugador agregado y procesado: ' + players[searched])
        else:
            print('Abortando import')
            quit()
    d["mu{0}".format(searched+1)] = float(rows[0][0])
    d["sigma{0}".format(searched+1)] = float(rows[0][1])

# Definir rankings
r1 = trueskill.Rating(mu=d.get("mu1"), sigma=d.get("sigma1"))
r2 = trueskill.Rating(mu=d.get("mu2"), sigma=d.get("sigma2"))
r3 = trueskill.Rating(mu=d.get("mu3"), sigma=d.get("sigma3"))
r4 = trueskill.Rating(mu=d.get("mu4"), sigma=d.get("sigma4"))

# Calcular rankings nuevos
rating_groups = [(r1,), (r2,), (r3,), (r4,)]
rated_rating_groups = trueskill.rate(rating_groups, ranks=[0, 1, 1, 1])
(r1,), (r2,), (r3,), (r4,) = rated_rating_groups
player_rankings = [r1, r2, r3, r4]

#-----------------
# Calculos decks
#-----------------
# Inicializar diccionario
d = {}

print("-----------------")
print("Descargando decks")
print("-----------------")

# Extraer data reciente de la base
for searched in range(0,len(decks)):
    print("Descargando data del mazo "+decks[searched])
    output = conn.execute("select mu,sigma from deck where name = '"+decks[searched]+"' and newest = 'Y'")
    rows = output.fetchall()
    if rows == []:
        agregar = input('Mazo desconocido: ' + decks[searched] + '. Agregar a la base de datos? (Y/N): ')
        if agregar == 'Y':
            insertNewDeck(decks[searched])
            output = conn.execute("select mu,sigma from deck where name = '"+decks[searched]+"' and newest = 'Y'")
            rows = output.fetchall()
            print('Nuevo mazo agregado y procesado: ' + decks[searched])
        else:
            print('Abortando import')
            quit()
    d["mu{0}".format(searched+1)] = float(rows[0][0])
    d["sigma{0}".format(searched+1)] = float(rows[0][1])

# Definir rankings
r1 = trueskill.Rating(mu=d.get("mu1"), sigma=d.get("sigma1"))
r2 = trueskill.Rating(mu=d.get("mu2"), sigma=d.get("sigma2"))
r3 = trueskill.Rating(mu=d.get("mu3"), sigma=d.get("sigma3"))
r4 = trueskill.Rating(mu=d.get("mu4"), sigma=d.get("sigma4"))

# Calcular ranking nuevo
rating_groups = [(r1,), (r2,), (r3,), (r4,)]
rated_rating_groups = trueskill.rate(rating_groups, ranks=[0, 1, 1, 1])
(r1,), (r2,), (r3,), (r4,) = rated_rating_groups
deck_rankings = [r1, r2, r3, r4]

print("------------------")
print("Cargando jugadores")
print("------------------")

# Borrar flags de newest e insertar los rankings nuevos
for searched in range(0,len(players)):
    print("Subiendo al jugador "+players[searched])
    output = conn.execute("update player set newest = null where name = '"+players[searched]+"' and newest = 'P'")
    output = conn.execute("update player set newest = 'P' where name = '"+players[searched]+"' and newest = 'Y'")
    query = conn.execute("insert into player values ('" + players[searched] + "','" + str(round(player_rankings[searched].mu,3)) + "','" + str(round(player_rankings[searched].sigma,3)) + "','" + date.today().strftime("%d-%b-%Y") + "','" + str(match_number) + "','Y','" + str(round(player_rankings[searched].mu,3) - 3*round(player_rankings[searched].sigma,3)) + "')")

print("--------------")
print("Cargando decks")
print("--------------")

for searched in range(0,len(decks)):
    print("Subiendo al mazo "+decks[searched])
    output = conn.execute("update deck set newest = null where name = '"+decks[searched]+"' and newest = 'P'")
    output = conn.execute("update deck set newest = 'P' where name = '"+decks[searched]+"' and newest = 'Y'")
    query = conn.execute("insert into deck values ('" + decks[searched] + "','" + str(round(deck_rankings[searched].mu,3)) + "','" + str(round(deck_rankings[searched].sigma,3)) + "','" + date.today().strftime("%d-%b-%Y") + "','" + str(match_number) + "','Y','" + str(round(deck_rankings[searched].mu,3) - 3*round(deck_rankings[searched].sigma,3)) + "')")
    
#-------------------------
# Insertar data del match
#-------------------------
# Ingresar match - el jugador 1 siempre es el ganador
for searched in range(0,len(players)):
    if searched == 0:
        winner = "Y"
    else:
        winner = "N"
    query = conn.execute("insert into match values ('" + date.today().strftime("%d-%b-%Y") + "','" + str(match_number) + "','" + players[searched] + "','" + decks[searched] + "','" + winner + "')")
