# Object-oriented-Programming_Project
  1. Realizacja animowanej wizualizacji ramienia robota
Zrealizować sterowalną przez użytkownika wizualizację wybranego ramienia robota (przykłady ramion
poniżej).Wizualizowane ramię (zwane dalej również modelem) musi posiadać co najmniej 3 stopnie swobody
(wizualizacja manipulatora nie jest konieczna ani nie jest wliczana do stopni swobody). Ruchy elementów
ramienia powinny odzwierciedlać rzeczywiste ruchy robota (np. kąt obrotu złącza w rzeczywistości jest
limitowany i nie może znacznie przekraczać kąta 360o
).
Wizualizowane ramię powinno umożliwiać interakcję z przynajmniej jednym elementem wirtualnego otoczenia
(elementem takim może być prymityw, czyli sfera bądź kostka), polegającą na przemieszczaniu tego elementu
(chwycenie, przemieszczenie, pozostawienie).
Interfejs sterujący powinien umożliwiać poruszanie poszczególnymi złączami bezpośrednio (w wyniku
naciśnięcia odpowiednich klawiszy), lecz również powinna istnieć możliwość wprowadzania położenia w
postaci liczbowej (wówczas ramie powinno wykonać animowany ruch do nowej pozycji). W przypadku ramion
cylindrycznego i polarnego, XY jest obligatoryjne).
Dodatkowo program powinien umożliwiać pracę w trybie uczenia i pracy – tak jak to ma miejsce w przypadku
„prawdziwych” robotów przemysłowych. Przykładowo: ramię robota w trybie uczenia przemieszcza
„prymitywa” z udziałem użytkownika, a po „nauczeniu” powtarza sekwencję ruchów.
