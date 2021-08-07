# CFR XML to SQL

Un script Python pentru convertirea
[fișierelor XML oferite de S.C. Informatica Feroviară S.A.](https://data.gov.ro/dataset?organization=sc-informatica-feroviara-sa)
într-o bază de date SQLite.

## Cum se folosește

- se plasează fișierele `.xml` în folderul `datafiles`
- (opțional) se completează fișierul `datafiles/mapping.json` cu numele companiilor
- se rulează `convert.py`:

```bash
# Unix
./convert.py
```

```powershell
# Windows
python convert.py
```

Scriptul este scris pentru Python 3.

## Schemă bază de date

Schema este validă pentru versiunea 2.

Coloanele fără tip de date sunt luate direct din XML (deci cel mai probabil tip text).

### Tabel **Meta**

Coloană  | Tip de date | Descriere
---------|-------------|----------
Versiune | int         | Versiunea bazei de date (schema aceasta descrie versiunea 2)

### Tabel **Companii**

Coloană   | Tip de date | Descriere
----------|-------------|----------
Id        | int pk      |
NumeLegal | text        | Numele oficial al companiei *(ex: S.C. Companie S.R.L)*
NumeComun | text        | Numele după care este cunoscută compania *(în general numele oficial fără prefix sau sufix; ex: Companie)*

### Tabel **Trenuri**

Coloană       | Tip de date | Descriere
--------------|-------------|----------
Number        | int pk      |
IdCompanie    | int         | fk Companii->Id
CategorieTren |             | R/IR/etc.
KmCum         | int         | Lungimea totală a traseului în **metri**
Lungime       | int         | Lungimea trenului
Numar         |             |
Operator      |             | ? - Uneori conține un număr unic pentru un anumit operator, alteori este gol
Proprietar    |             |
Putere        |             |
Rang          |             |
Servicii      |             |
Tonaj         |             |

### Tabel **Trase**

Coloană           | Tip de date | Descriere
------------------|-------------|----------
NumarTren         | int         | fk Trenuri->Number
Id                | int         | Id trasă (1, 2, ...)
Tip               |             |
CodStatieInitiala | int         | fk Statii->CodStatie
CodStatieFinala   | int         | fk Statii->CodStatie

### Tabel **Statii**

Coloană   | Tip de date | Descriere
----------|-------------|----------
CodStatie | int pk      | Codul folosit în setul de date
Denumire  | text        | Numele stației *(ex: București Nord Gr.A)*

### Tabel **ElementeTrasa**

Coloană           | Tip de date | Descriere
------------------|-------------|----------
NumarTren         | int         | fk Trenuri->Number + Trase->NumarTren
IdTrasa           | int         | fk Trase->Id
Secventa          | int         | Ordinea secvenței în trasă (1, 2, ...)
Ajustari          |             |
CodStaDest        |             | fk Statii->CodStatie
CodStaOrigine     |             | fk Statii->CodStatie
DenStaDestinatie  |             |
DenStaOrigine     |             |
Km                | int         | Distanța în **metri** între stații *(ex: 3022 -> 3022 m / 3 km)*
Lungime           | int         | Lungimea trenului
OraP              | int         | Ora plecării (numărul de secunde de la 00:00:00 în ziua primei plecări)
OraS              | int         | Ora sosirii (numărul de secunde de la 00:00:00 în ziua primei plecări)
Rci               |             |
Rco               |             |
Restrictie        |             |
StationareSecunde | int         | Numărul de secunde de staționare *în stația origine*
TipOprire         |             |
Tonaj             |             |
VitezaLivret      | int         | Viteza între stația origine și destinație în km/h
