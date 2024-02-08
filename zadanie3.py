import requests
import json
import sys
import re
from datetime import date, datetime, timedelta

faktura = {}
wplaty = []
waluty = []
data_regex = re.compile("^20[0-2][0-9]-((0[1-9])|(1[0-2]))-(0[1-9]|[1-2][0-9]|3[0-1])$") # regex do sprawdzenia poprawności daty w formacie RRRR-MM-DD

# Pozyskanie tabeli walut dostępnych w API NBP
tabela_walut = requests.get("https://api.nbp.pl/api/exchangerates/tables/a/")
if tabela_walut.status_code != 200:
    print("Program nie mógł pozyskać tabeli walut")
    input("Wciśnij Enter aby opuścić program")
    sys.exit()
else:
    for waluta in tabela_walut.json()[0]['rates']:
        waluty.append(waluta['code'])

print("Dostępne waluty:")
print(waluty)

# Wprowadzanie danych w trybie interaktywnym
if len(sys.argv) == 1:
    print("\nWprowadź informacje o fakturze:")
    faktura["kwota"] = input("Kwota: ")
    faktura["waluta"] = input("Waluta: ")
    if faktura["waluta"].upper() not in waluty:
        print(f"Waluta {faktura['waluta'].upper()} nie znajduje się w tabeli walut")
        input("Wciśnij Enter aby opuścić program")
        sys.exit()
    faktura["data"] = input("Data (rrrr-mm-dd): ")
    if bool(data_regex.fullmatch(faktura["data"])) != True:
        print("Wprowadzono datę nieprawdziwą lub w formacie innym niż RRRR-MM-DD")
        input("Wciśnij Enter aby opuścić program")
        sys.exit()
    
    iloscwplat = int(input("\nWprowadź ilość wpłat:"))
    print("Wprowadź informacje o wpłatach:")
    for i in range(iloscwplat):
        wplaty.append({})
        print(f"\nWpłata nr {i+1}:")
        wplaty[i]["kwota"] = input("Kwota: ")
        wplaty[i]["waluta"] = input("Waluta: ")
        if wplaty[i]["waluta"].upper() not in waluty:
            print(f"Waluta {wplaty[i]['waluta'].upper()} nie znajduje się w tabeli walut")
            input("Wciśnij Enter aby opuścić program")
            sys.exit()
        wplaty[i]["data"] = input("Data (rrrr-mm-dd): ")
        if bool(data_regex.fullmatch(wplaty[i]["data"])) != True:
            print("Wprowadzono datę nieprawdziwą lub w formacie innym niż RRRR-MM-DD")
            input("Wciśnij Enter aby opuścić program")
            sys.exit()
# Wprowadzanie danych w trybie wsadowym
elif len(sys.argv) == 2:
    with open(sys.argv[1]) as f:
        segmenty = f.readlines()

        segment_faktury = segmenty[0].strip().split(", ")
        faktura["kwota"] = segment_faktury[0]
        faktura["waluta"] = segment_faktury[1]
        if faktura["waluta"].upper() not in waluty:
            print(f"Waluta {faktura['waluta'].upper()} nie znajduje się w tabeli walut")
            input("Wciśnij Enter aby opuścić program")
            sys.exit()
        faktura["data"] = segment_faktury[2]
        if bool(data_regex.fullmatch(faktura["data"])) != True:
            print("Wprowadzono datę nieprawdziwą lub w formacie innym niż RRRR-MM-DD")
            input("Wciśnij Enter aby opuścić program")
            sys.exit()

        i = 0
        for wplata in segmenty[1:]:
            wplaty.append({})
            segment_wplaty = wplata.strip().split(", ")
            wplaty[i]["kwota"] = segment_wplaty[0]
            wplaty[i]["waluta"] = segment_wplaty[1]
            if wplaty[i]["waluta"].upper() not in waluty:
                print(f"Waluta {wplaty[i]['waluta'].upper()} nie znajduje się w tabeli walut")
                input("Wciśnij Enter aby opuścić program")
                sys.exit()
            wplaty[i]["data"] = segment_wplaty[2]
            if bool(data_regex.fullmatch(wplaty[i]["data"])) != True:
                print("Wprowadzono datę nieprawdziwą lub w formacie innym niż RRRR-MM-DD")
                input("Wciśnij Enter aby opuścić program")
                sys.exit()
            i+=1
else:
    print("Wprowadzono niepoprawną ilość argumentów")
    input("Wciśnij Enter aby opuścić program")
    sys.exit()

def pozyskajKurs(waluta, data):

    # Jeżeli waluta to PLN zawsze zwraca 1
    if waluta.lower() == "pln":
        return 1
    
    i = 5 # Maksymalnie ile dni wstecz program ma szukać dostępnych kursów, jeżeli nie są dostępne na podaną datę
    data_objekt = datetime.strptime(data, '%Y-%m-%d').date()

    odpowiedz = requests.get(f"https://api.nbp.pl/api/exchangerates/rates/a/{waluta}/{data}")

    if odpowiedz.status_code != 200: # Jeżeli program nie znajdzie kursów na daną datę zacznie szukać najbliższego dnia roboczego gdzie są dostępne
        for dni in range(i):
            data_objekt -= timedelta(days=1)
            data = data_objekt.strftime("%Y-%m-%d")
            odpowiedz = requests.get(f"https://api.nbp.pl/api/exchangerates/rates/a/{waluta}/{data}")
            if odpowiedz.status_code == 200:
                print(f"Najbliższy dzień roboczy dla którego udało się znaleźć kurs: {data}")
                return odpowiedz.json()['rates'][0]['mid']
        print("Nie udało się znaleźć kursu waluty z danego dnia ani najbliższych poprzednich dni")
        input("Wciśnij Enter aby opuścić program")
        sys.exit()
    else:
        return odpowiedz.json()['rates'][0]['mid']

def obliczRoznice(faktura, wplaty):

    # Obliczając różnicę kursową, liczymy na podstawie kursu dnia roboczego poprzedzającego datę faktury
    faktura["data"] = (datetime.strptime(faktura["data"], '%Y-%m-%d').date() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("\nSzukanie kursu dla faktury\n")
    kursFaktura = pozyskajKurs(faktura["waluta"], faktura["data"])
    print(f"Kurs dla faktury: {kursFaktura}")
    kwotaFaktury = round(kursFaktura * float(faktura["kwota"]), 2)

    print("\nSzukanie kursu dla wpłat\n")
    kursWplat = []
    kwotaWplat = 0
    for wplata in wplaty:
        kursWplat.append(pozyskajKurs(wplata["waluta"], wplata["data"]))
        print(f"Kurs dla wpłaty nr {wplaty.index(wplata) + 1}: {kursWplat[wplaty.index(wplata)]}\n")
        kwotaWplat += kursWplat[wplaty.index(wplata)] * float(wplata["kwota"])
    kwotaWplat = round(kwotaWplat, 2)

    print("- - - - - - - - - - - - - - - -\n")
    print(f"Kwota faktury w PLN: {kwotaFaktury}")
    print(f"Łączna kwota wpłat w PLN: {kwotaWplat}\n")

    if kwotaWplat >= kwotaFaktury:
        print("Faktura została w pełni opłacona")
    if kwotaWplat > kwotaFaktury:
        nadplata = round(kwotaWplat - kwotaFaktury, 2)
        print(f"Należne jest {nadplata} PLN nadpłaty do zwrotu")
    if kwotaWplat < kwotaFaktury:
        doplata = round(kwotaFaktury - kwotaWplat, 2)
        print(f"Należy dopłacić {doplata} PLN") 

obliczRoznice(faktura, wplaty)

input()
