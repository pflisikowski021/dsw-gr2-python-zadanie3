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