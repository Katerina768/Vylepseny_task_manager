import pymysql  # pracuji s knihovnou pymysql, protože mysql mi nefungovala

# funkce k vytvoření databáze, pokud selže, zobrazí se chybová hláška
def vytvor_databazi():
    try:
        spojeni = pymysql.connect(host="localhost", user="root", password="1111")  # připojení k pymysql serveru
        kurzor = spojeni.cursor()
        kurzor.execute("CREATE DATABASE IF NOT EXISTS ukolnik") # vytvoření databáze ukolnik, pokud neexistuje
        spojeni.commit() # potvrzení změn
        kurzor.close()
        spojeni.close()
    except pymysql.MySQLError as err:
        print(f"Chyba při vytváření databáze: {err}") # výpis chyby v případě selhání

# funkce k připojení k databázi, pokud připojení selže, zobrazí chybovou hlášku
def pripojeni_db():
    try:
        spojeni = pymysql.connect(
            host="localhost",
            user="root",
            password="1111",
            database="ukolnik" # připojení k databázi ukolnik
        )
        return spojeni 
    except pymysql.MySQLError as err:
        print(f"Chyba při připojení k databázi: {err}")
        return None

# funkce vytvoří tabulku, pokud již neexistuje, v případě chyby zobrazí chybovou hlášku
def vytvoreni_tabulky(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ukoly (
                id INT AUTO_INCREMENT PRIMARY KEY, # unikátní id úkolu
                nazev VARCHAR(255),
                popis TEXT,
                stav ENUM('nezahájeno', 'hotovo', 'probíhá') DEFAULT 'nezahájeno', # výčet možných stavů
                datum_vytvoreni DATETIME DEFAULT CURRENT_TIMESTAMP # automatické nastavení data vytvoření
            )
        ''')
    except pymysql.MySQLError as err:
        print(f"Chyba při vytváření tabulky: {err}")

# funkce hlavního menu programu, která odkazuje na jednotlivé hlavní funkce programu z menu 
# pokud uživatel zadá neplatnou volbu, program ho upozorní a nechá ho vybrat znovu
def hlavni_menu():
    vytvor_databazi()         # zavolání funkce k vytvoření databáze a následnému spojení s ní
    spojeni = pripojeni_db()
    if spojeni is None:
        return # pokud připojení selže, program se ukončí

    cursor = spojeni.cursor()
    vytvoreni_tabulky(cursor)   # zavolání funkce k vytvoření tabulky, pokud ještě není

    try:
        while True: 
            # výpis hlavního menu
            print("\nHlavní menu:") 
            print("1. Přidat úkol")
            print("2. Zobrazit úkoly")
            print("3. Aktualizovat úkol")
            print("4. Odstranit úkol")
            print("5. Ukončit program")

            volba = input("\nZadejte číslo volby (1–5): ").strip() # vstup od uživatele k zadání hodnoty

            # reakce podle volby uživatele
            if volba == "1":
                pridat_ukol(cursor)
                spojeni.commit()
            elif volba == "2":
                zobrazit_ukoly(cursor)
            elif volba == "3":
                aktualizovat_ukol(cursor)
                spojeni.commit()
            elif volba == "4":
                odstranit_ukol(cursor)
                spojeni.commit()
            elif volba == "5":
                print("Ukončuji program.")
                break # konec smyčky
            else:
                print("\nNeplatná volba! Zadejte číslo od 1 do 5.")
               

    except pymysql.MySQLError as err:       # ošetření pro případ chyby v programu, vypíše se chybová hláška
        print(f"Došlo k chybě v programu: {err}")

    finally:
        cursor.close()  # uzavření spojení s databází
        spojeni.close()
        print("Spojení s databází bylo uzavřeno.")

# funkce má za úkol přidat název, popis a stav úkolu s povinným vstupem od uživatele
def pridat_ukol(cursor):
    print("\nZadejte nový úkol:")

    # smyčka pro název - zamezení prázdného vstupu
    while True:
        nazev = input("Název úkolu: ").strip()
        popis = input("Popis úkolu: ").strip()
        
        # kontrola platnosti vstupu a pokud nejsou hodnoty prázdné, uloží se do tabulky
        if popis == "" or nazev == "":
            print("Zadaný název nebo popis je prázdný. Prosím vyplňte.")
        else:
            break      
            

    povolene_stavy = ['nezahájeno', 'hotovo', 'probíhá']
    stav = ""
    while stav not in povolene_stavy:   # smyčka k přidání povoleného stavu
        stav = input("Stav (nezahájeno, hotovo, probíhá): ").strip().lower() # vstup od uživatele k zadání stavu
        if stav not in povolene_stavy:
            print(f"Neplatný stav. Povolené hodnoty jsou: {povolene_stavy}") # ošetření, že je možné zadat pouze povolený stav

    try:
        sql = "INSERT INTO ukoly (nazev, popis, stav) VALUES (%s, %s, %s)" # vložení hodnot do tabulky
        cursor.execute(sql, (nazev, popis, stav))
        print(f" Úkol '{nazev}' byl přidán.")
    except pymysql.MySQLError as err: # v případě chyby program zobrazí chybovou hlášku
        print(f" Chyba při ukládání úkolu: {err}")

# funkce pro zobrazení všech úkolů
def zobrazit_ukoly(cursor):
    print("\n Jaké úkoly si přejete zobrazit?")
    print("1. Všechny úkoly")  # informace, že program umožňuje vybrat zobrazení všech úkolů
    print("2. Pouze aktivní úkoly (Nezahájeno / Probíhá)")  # volba čísla 2 zobrazí vyfiltrované aktivní úkoly

    volba = input("Zadejte číslo volby (1 nebo 2): ").strip() # vstup od uživatele k vybrání volby

    if volba == "1":
        dotaz = "SELECT id, nazev, popis, stav FROM ukoly"
        popis_filtru = "Všechny úkoly"
    elif volba == "2":
        dotaz = "SELECT id, nazev, popis, stav FROM ukoly WHERE stav IN ('nezahájeno', 'probíhá')"
        popis_filtru = "Aktivní úkoly (Nezahájeno / Probíhá)"
    else:
        print("Neplatná volba. Zobrazení úkolů bylo zrušeno.")
        return

    try:
        cursor.execute(dotaz)
        vysledky = cursor.fetchall()

        print(f"\n {popis_filtru}:")
        if not vysledky:  # pokud seznam úkolů je prázdný, program uživatele upozorní
            print("Seznam úkolů je prázdný.")
            return

        for ukol in vysledky: # zobrazí zvolený seznam úkolů, pokud není prázdný
            id, nazev, popis, stav = ukol
            print(f"{id}. {nazev} | {popis} | {stav}")

    except pymysql.MySQLError as err: # v případě chyby zobrazí program chybovou hlášku
        print(f" Chyba při načítání úkolů: {err}")

# funkce k autalizaci úkolů, zobrazí seznam úkolů a umožňuje vybrat nový stav "Probíhá" nebo "Hotovo"
def aktualizovat_ukol(cursor):
    try:
        cursor.execute(f"SELECT id, nazev, stav FROM ukoly") # příkaz zobrazí id, název, stav z tabulky ukoly
        ukoly = cursor.fetchall()
    
        if not ukoly:
            print("Nejsou žádné úkoly k aktualizaci.") # pokud je seznam úkolů prázdný, program o tom informuje
            return
    
        print("\n Seznam úkolů: ")  # zobrazí se seznam úkolů
        for id, nazev, stav in ukoly:
            print(f"{id}. {nazev} | {stav}")
    
        platna_id = {id for id, _, _ in ukoly} # vytvoření množiny platných ID úkolů z načtených úkolů

        while True:
            vstup = input("\nZadejte ID úkolu, které chcete aktualizovat: ").strip() # načtení vstupu od uživatele
            if vstup.isdigit(): # kontrola, zda vstup obsahuje jen číslice
                id_ukolu = int(vstup)
                # kontrola, že je zadané ID v množině platných ID
                if id_ukolu in platna_id:
                    break # pokud ano, smyčka se ukončí
    
            print("Zadané ID neexistuje. Vyberte prosím znovu.") # pokud vstup není platné číslo nebo ID neexistuje, zobrazí se upozornění

        # smyčka pro zadání nového stavu úkolu
        while True:
            novy_stav = input("Zadejte nový stav (probíhá, hotovo): ").strip().lower() # vstup od uživatele slouží k zadání nového stavu - probíhá, hotovo
            if novy_stav in ['probíhá', 'hotovo']:
                break
            else:
                print("Neplatný stav. Zadejte znovu.")
            
    
        cursor.execute(f"UPDATE ukoly SET stav = %s  WHERE id = %s", (novy_stav, id_ukolu)) # aktualizace hodnot v tabulce
        print("Stav úkolu byl aktualizován.") 

    except pymysql.MySQLError as err:  # v případě chyby se zobrazí chybová hláška
        print(f"Chyba při aktualizaci úkolu: {err}")


def odstranit_ukol(cursor):
    try:
        cursor.execute("SELECT id, nazev, popis, stav, DATE(datum_vytvoreni) FROM ukoly")
        ukoly = cursor.fetchall()

        if not ukoly:
            print("\nNejsou žádné úkoly k odstranění.")
            return
        
        print("\nSeznam úkolů: ")
        for id, nazev, popis, stav, datum_vytvoreni in ukoly:
            print(f"{id}. {nazev} | {popis} | {stav} | {datum_vytvoreni}")

        

        existujici_id = [str(ukol[0]) for ukol in ukoly]
        while True:
            volba_ukolu = input(f"\nZadejte id úkolu, který chcete odstranit: ").strip()
            if volba_ukolu in existujici_id:
                break
            else:
                print("Neexistující ID. Zkuste to znovu.")
        
        cursor.execute("DELETE FROM ukoly WHERE id = %s", (volba_ukolu,))
       
        print("\nÚkol byl odstraněn.")
    
                   
    except pymysql.MySQLError as err:
        print(f"Chyba při mazání úkolu: {err}")


        

# Spuštění programu
if __name__ == "__main__":
   hlavni_menu()