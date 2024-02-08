# Dokumentacja
Program pozwala na obliczenie różnicy kursowej dla podanej faktury i dowolnej ilości wpłat.

### Sposoby użycia programu:
#### Interaktywny

- Po uruchomieniu, program pyta o uzupełnienie informacji na temat:
    - Szczegółów faktury
    - Ilości wpłat
    - Szczegółów wpłat

- Poszczególne pola i jak je wypełnić:
    - Kwota - dowolna liczba (miejsca dziesiętne podajemy po kropce)
    - Waluta - wypełniamy 3-znakowym kodem waluty z listy, która wyświetla się po otworzeniu programu
    - Data - istniejąca data w formacie RRRR-MM-DD w zakresie od 2 stycznia 2002 do dnia dzisiejszego
    - Ilość wpłat - dowolna liczba dodatnia całkowita

Po wprowadzeniu informacji program znajdzie kursy dla podanych dat (lub dla najbliższego dnia roboczego, jeżeli podana data to weekend/święto i nie ma dostępnych danych),
a następnie obliczy różnicę kursową i poda kwotę nadpłaty lub dopłaty, jeżeli będzie ona potrzebna

#### Wsadowy

Aby użyć programu w trybie wsadowym musimy posiadać plik tekstowy w formacie:

```
<kwota>, <waluta>, <rrrr-mm-dd> # Faktura
<kwota>, <waluta>, <rrrr-mm-dd> # Wpłata
... # Kolejne wpłaty
```

Przykładowy plik z danymi (załączony również w repozytorium):

```
10, usd, 2010-10-10
2, cad, 2010-11-20
2, cad, 2011-11-20
2.5, cad, 2012-11-20
```

Tak sformatowany plik możemy następnie przeciągnąć na program lub podać jego ścieżkę jako argument przy uruchamianiu programu w konsoli.
Program wtedy uruchomi się z danymi z pliku i obliczy na ich podstawię różnicę kursową oraz poda kwotę nadpłaty lub dopłaty, jeżeli będzie ona potrzebna

# Raport z zadania

## Cel zadania

Celem zadania było stworzenie programu do obliczenia różnic kursowych dla faktury i wpłat.

Różnice kursowe obliczam w programie według definicji ze strony https://www.fakturaxl.pl/jak-obliczac-roznice-kursowe

```
"Zgodnie z polskim prawem różnicą kursową jest różnica pomiędzy:
- wartością faktury w walucie obcej w PLN (przeliczoną po średnim kursie danej waluty ogłoszonym przez NBP w ostatnim dniu roboczym poprzedzającym dzień powstania obowiązku  podatkowego)
- wartością w złotówkach, faktycznie zapłaconej kwoty z tytułu danego zobowiązania wg średniego kursu ogłoszonego przez NBP w dniu dokonania zapłaty."
```

## Przebieg tworzenia programu

#### Tworzenie programu zacząłem od funkcji pozyskania kursu PLN dla danej waluty i daty:

```python
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
    else:
        return odpowiedz.json()['rates'][0]['mid']
```

Na początku funkcja ta szukała kursów tylko dla bezpośrednio podanej daty i sprawdzałem jej działanie wywołując ją z hard-coded zmiennymi.
Zauważyłem problem gdzie funkcja nie mogła znaleźć kursów dla niektórych dat, ponieważ były to dni robocze lub święta, więc zastosowałem
system szukania najbliższego poprzedniego dnia roboczego, gdzie limit jak daleko program szuka można ustawić zmieniając wartość zmiennej `i`.

Na początku konwertuję podaną datę w objekt typu datetime, aby móc go użyć do zmieniania daty jeżeli zajdzie taka potrzeba
```python
data_objekt = datetime.strptime(data, '%Y-%m-%d').date()
```
Następnie jeżeli program nie znajdzie kursów dla danej daty, używam stworzonego objektu datetime aby odjąć od niego jeden dzień i przekonwertować go
spowrotem na string z datą, nadpisując zmienną `data`
```python
data_objekt -= timedelta(days=1)
data = data_objekt.strftime("%Y-%m-%d")
```
Program następnie szuka dla tej daty kursów i jeżeli nie może ich znaleźć to powtarza tą czynność aż do określonego limitu

#### Następnym krokiem jaki obrałem przy tworzeniu programu było stworzenie systemu wprowadzania danych:

Zacząłem od metody uruchamiania programu razem z danymi metodą wsadową, ponieważ w ten sposób prościej i szybciej było testować kod.
Postanowiłem stworzyć plik tekstowy gdzie pierwszą linijką była faktura a następnymi wpłaty, a następnie stworzyłem metodę parsowania tego pliku w programie
i ustalania z jego danych wartości zmiennych.

Jeżeli przy uruchamianiu programu został wprowadzony argument program uruchomi się w trybie wsadowym:
```python
elif len(sys.argv) == 2:
```

Następnie program otwiera plik wprowadzony jako argument i dzieli go na segmenty (każda linijka to jeden segment)

```python
with open(sys.argv[1]) as f:
        segmenty = f.readlines()
```

Pierwszy segment pliku to faktura, więc splituje dane po przecinku i zapisuje je do odpowiednich kluczy dla faktury, jednocześnie sprawdzając poprawność danych
```python
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
```

Następnie dla pozostałych segmentów wykonuje to samo tylko zapisuje to do wpłat, które tworzone są w liscie `wplaty`
```python
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
```

Później stworzyłem też metodę wprowadzania danych interaktywną, która uruchamia się gdy przy uruchamianiu programu nie został podany żaden argument:
```python
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
```

Dane tak samo zapisywane są do faktury i do wpłat tworzonych na liście `wplaty`, jednak dane pozyskiwane są od użytkownika, który wpisuje je w konsoli

W obu przypadkach, jak można zauważyć, weryfikowana jest poprawność wprowadzonych danych.
Weryfikowana jest ona z regexem daty
```python
data_regex = re.compile("^20[0-2][0-9]-((0[1-9])|(1[0-2]))-(0[1-9]|[1-2][0-9]|3[0-1])$")
```
Oraz z dostępnością kursów w API NBP
```python
waluty = []

tabela_walut = requests.get("https://api.nbp.pl/api/exchangerates/tables/a/")
if tabela_walut.status_code != 200:
    print("Program nie mógł pozyskać tabeli walut")
    input("Wciśnij Enter aby opuścić program")
    sys.exit()
else:
    for waluta in tabela_walut.json()[0]['rates']:
        waluty.append(waluta['code'])
```

#### Ostatnim krokiem stworzenia programu było samo obliczenie różnicy kursowej:

```python
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
```

Funkcja ta na samym początku odejmuje jeden dzień od daty faktury.
```python
faktura["data"] = (datetime.strptime(faktura["data"], '%Y-%m-%d').date() - timedelta(days=1)).strftime("%Y-%m-%d")
```
Jest to związane z definicją różnicy kursowej, gdzie kurs faktury powinien być sprawdzany na ostatni dzień roboczy przed wystawieniem faktury.

Następnie funkcja wywołuje funkcję `pozyskajKurs` dla danych z faktury i każdej wpłaty i wyświetla pozyskane kursy, jednocześnie obliczając kwotę faktury w PLN
i łączną kwotę wpłat w PLN
```python
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
```

Na samym końcu wyświetlane są łączne kwoty faktury i wpłat w PLN i na ich podstawie wyświetlana jest dopłata, niedopłata lub ich brak:
```python
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
```


