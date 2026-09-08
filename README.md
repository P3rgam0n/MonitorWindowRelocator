# 🖥️ Monitor Window Relocator

Narzędzie dla systemu Windows rozwiązujące problem okien aplikacji otwierających się na wyłączonych / uśpionych monitorach w konfiguracjach wielomonitorowych (np. 3 monitory).

---

## 🚀 Jak to działa?

Gdy używasz 1 lub 2 monitorów z posiadanych 3, system Windows może pamiętać pozycję otwieranego programu i renderować jego okno na monitorze, który fizycznie jest wyłączony. 

**Monitor Window Relocator** pozwala w szybki i prosty sposób przenieść dowolne okno na aktywny ekran za pomocą skrótu klawiszowego, kliknięcia w menu lub automatycznego skanowania.

---

## ⌨️ Skróty Klawiszowe (Global Hotkeys)

Program działa w tle i reaguje na skróty klawiszowe w dowolnym momencie:

| Skrót | Działanie |
| :--- | :--- |
| **`Ctrl + Alt + M`** | **Przenieś aktywne okno na monitor, na którym znajduje się kursor myszy.** |
| **`Ctrl + Alt + G`** | **Ściągnij wszystkie ukryte / niewidoczne okna z wyłączonych monitorów na Ekran Główny.** |
| **`Ctrl + Alt + 1`** | **Przenieś aktywne okno na Monitor 1.** |
| **`Ctrl + Alt + 2`** | **Przenieś aktywne okno na Monitor 2.** |
| **`Ctrl + Alt + 3`** | **Przenieś aktywne okno na Monitor 3.** |

---

## 🛠️ Uruchamianie

1. **Uruchomienie interfejsu graficznego (GUI)**:
   - Kliknij dwukrotnie w plik `Uruchom_Program.bat` lub wpisz w konsoli:
     ```cmd
     python main.py
     ```

2. **Szybkie ściągnięcie okien z wiersza poleceń / skrótu (bez otwierania GUI)**:
   - Kliknij dwukrotnie w plik `Sciagnij_Niewidoczne_Okna.bat` lub wpisz:
     ```cmd
     python main.py --gather
     ```

---

## 📁 Struktura Plików

- `relocator_core.py` – Natywna obsługa API Windows Win32 (detekcja monitorów, pozycja kursora myszy, skalowanie i przesuwanie okien).
- `hotkey_manager.py` – Menedżer skrótów klawiszowych rejestrowanych w systemie Windows (`RegisterHotKey`).
- `app_gui.py` – Interfejs graficzny aplikacji (Tkinter / ttk) z listą otwartych okien i przyciskami sterowania.
- `main.py` – Plik główny programu.
- `Uruchom_Program.bat` – Skrypt uruchamiający program w tle.
- `Sciagnij_Niewidoczne_Okna.bat` – Skrypt do natychmiastowego zgarniania niewidocznych okien.
