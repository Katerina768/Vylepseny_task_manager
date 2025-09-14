
import pytest
import pymysql
from unittest.mock import patch
from ukoly import pridat_ukol, aktualizovat_ukol, odstranit_ukol

# vytvoření databáze
def vytvor_databazi():
    try:
        spojeni = pymysql.connect(host="localhost", user="root", password="1111")  # připojení k pymysql serveru
        kurzor = spojeni.cursor()
        kurzor.execute("CREATE DATABASE IF NOT EXISTS test_ukolnik") # vytvoření databáze ukolnik, pokud neexistuje
        spojeni.commit() # potvrzení změn
        kurzor.close()
        spojeni.close()
    except pymysql.MySQLError as err:
        print(f"Chyba při vytváření databáze: {err}")



# fixture pro připojení k databázi a nastavení testovacího prostředí
@pytest.fixture(scope="function")
def db_nastaveni():

# zavolání funkce pro vytvoření databáze
    vytvor_databazi()
    
# připojení k databázi
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="1111",
        database="test_ukolnik"
)

    cursor = conn.cursor()

# vytvoření testovací tabulky
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS ukoly (
                id INT AUTO_INCREMENT PRIMARY KEY, # unikátní id úkolu
                nazev VARCHAR(255),
                popis TEXT,
                stav ENUM('nezahájeno', 'hotovo', 'probíhá') DEFAULT 'nezahájeno', # výčet možných stavů
                datum_vytvoreni DATETIME DEFAULT CURRENT_TIMESTAMP # automatické nastavení data vytvoření
            )
        ''')
    
    conn.commit()

    # předání připojení a kurzoru testům
    yield conn, cursor

    # úklid po testech: Smazání tabulky
    cursor.execute("DROP TABLE IF EXISTS ukoly")
    conn.commit()

    # uzavření připojení
    cursor.close()
    conn.close()


# AUTOMATIZOVANÉ POZITIVNÍ TESTY

# 1. Test: Ověření vložení dat
def test_validni_vlozeni(db_nastaveni):
    conn, cursor = db_nastaveni

    # vložení platného záznamu
    cursor.execute("INSERT INTO ukoly (nazev, popis) VALUES ('Validní', 'testovací')")
    conn.commit()
    cursor.execute("SELECT * FROM ukoly WHERE nazev = 'Validní'")
    vysledek = cursor.fetchone()
    assert vysledek is not None, "Záznam nebyl vložen do tabulky"
    assert vysledek[1] == "Validní", "Název není správný."
    assert vysledek [2] == "testovací", "Popis není správný."

# 2. Test: Ověření aktualizace dat
def test_aktualizace_dat(db_nastaveni):
    conn, cursor = db_nastaveni

    # vložení testovacího záznamu
    cursor.execute("INSERT INTO ukoly (nazev, stav) VALUES ('Validní', 'hotovo')")
    conn.commit()

    # aktualizace dat
    cursor.execute("UPDATE ukoly  SET stav = 'hotovo'  WHERE nazev = 'Validní'")
    conn.commit()

    # ověření aktualizace
    cursor.execute("SELECT * FROM ukoly WHERE nazev = 'Validní'")
    vysledek = cursor.fetchone()
    assert vysledek[3] == 'hotovo', "Stav nebyl správně aktualizován."

# 3. Test: Ověření mazání dat
def test_mazani_dat(db_nastaveni):
    conn, cursor = db_nastaveni

    # vložení testovacího záznamu
    cursor.execute("INSERT INTO ukoly (nazev, popis) VALUES ('Validní', 'testovací')")
    conn.commit()

    # smazání záznamu
    cursor.execute("DELETE FROM ukoly WHERE nazev = 'Validní'")
    conn.commit()

    # ověření mazání
    cursor.execute("SELECT * FROM ukoly WHERE nazev = 'Validní'")
    vysledek = cursor.fetchall()
    assert len(vysledek) == 0, "Záznam nebyl správně smazán."


# AUTOMATIZOVANÉ NEGATIVNÍ TESTY

# 1. Test: Ověření chyby při vložení neplatných dat
def test_nevalidni_vlozeni(db_nastaveni):
    conn, cursor = db_nastaveni

    # pokus o vložení příliš dlouhého textu
    with pytest.raises(pymysql.err.DataError, match="too long"):
        cursor.execute("INSERT INTO ukoly (nazev, popis) VALUES (%s, %s)", ('a' * 300, 'test'))
        conn.commit()

# 2. Test: Ověření 
def test_nevalidni_aktualizace(db_nastaveni):
    conn, cursor = db_nastaveni
    
    #  vytvoření testovacího záznamu
    cursor.execute("INSERT INTO ukoly (nazev, stav) VALUES ('Test', 'nezahájeno')")
    conn.commit()

    # získání ID nově vloženého záznamu
    cursor.execute("SELECT id FROM ukoly WHERE nazev = 'Test'")
    id_ukolu = cursor.fetchone()[0]

    with patch('builtins.input', side_effect=[str(id_ukolu), "zrušeno", "hotovo"]):
        aktualizovat_ukol(cursor)
        conn.commit()

    # ověření výsledku
    cursor.execute("SELECT stav FROM ukoly WHERE id = %s", (id_ukolu,))
    stav = cursor.fetchone()[0]
    assert stav == "hotovo"

    
# 3. Test: Ověření mazání neexistujícího záznamu
def test_mazani_neexistujiciho_zaznamu(db_nastaveni):
    conn, cursor = db_nastaveni

    # Počet záznamů před testem
    cursor.execute("SELECT count(*) FROM ukoly")
    pocatecni_pocet = cursor.fetchone()[0]

    # mazání neexistujícího záznamu
    cursor.execute("DELETE FROM ukoly WHERE nazev = 'Nevložený'")
    conn.commit()

    # počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly")
    finalni_pocet = cursor.fetchone()[0]

    # ověření, že počet záznamů zůstal stejný
    assert pocatecni_pocet == finalni_pocet, "Mazání neexistujícího záznamu."








