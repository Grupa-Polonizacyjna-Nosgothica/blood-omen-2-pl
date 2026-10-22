# Blood Omen 2 PL - łatka dodająca napisy + spolszczenie

Nieoficjalna poprawka dodająca napisy do dialogów i scenek w grze `Legacy of Kain: Blood Omen 2` (wersja na PC), autorstwa Grupy Polonizacyjnej Nosgothica.
Docelowo z polskim tłumaczeniem.

Wersja na PC nie wyświetla napisów do dialogów. Silnik gry ma co prawda kompletny system napisów, ale został on wyłączony i nie ma do niego żadnych tekstów.
Nasza poprawka go włącza i dodaje polskie teksty.

## Status prac: **w toku, bez daty wydania**

| Część | Stan |
|---|---|
| Wyświetlanie napisów w grze | działa (sprawdzone w otwierającej scenie Slumsów) |
| Instalator | napisany, jeszcze nie sprawdzony na Windows |
| Polskie litery (ą ć ę ł ń ś ź ż) w czcionce gry | w przygotowaniu |
| Polskie napisy | w przygotowaniu |

Do czasu wydania nie ma gotowego instalatora do pobrania. Gdy się pojawi, znajdziesz go w zakładce [Releases](https://github.com/Grupa-Polonizacyjna-Nosgothica/blood-omen-2-pl/releases).

## Instalacja

1. Zamknij grę i launcher.
2. Pobierz `BO2-PL-Setup-<wersja>.exe` z zakładki [Releases](https://github.com/Grupa-Polonizacyjna-Nosgothica/blood-omen-2-pl/releases) i uruchom go (potrzebne są uprawnienia administratora, bo gry często leżą w chronionych folderach).
3. Instalator sam znajdzie grę (GOG, a także Steam). Jeśli mu się nie uda, wskaż główny folder gry, czyli ten z plikiem `bo2.exe`.
4. Uruchom grę. Napisy pojawiają się u dołu ekranu podczas dialogów.

Instalator **nie zawiera plików gry**. Zmienia na twoim komputerze kilka bajtów w twoim pliku `bo2.exe` i kopiuje pliki z napisami do folderu `data\texts` w folderze gry.
Przed zmianą tworzy kopię zapasową `bo2.exe.plbackup` obok pliku gry.

**Obsługiwana wersja gry:** wersja z GOG. Instalator sprawdza plik gry i odmówi zmiany pliku z inną wersją. Wersja ze Steam nie była testowana.

## Po aktualizacji lub sprawdzeniu plików gry

Sprawdzenie integralności plików w GOG Galaxy lub Steam przywraca oryginalny `bo2.exe` i usuwa poprawkę.
Wystarczy wtedy uruchomić skrót **Zastosuj spolszczenie ponownie** z menu Start.

## Odinstalowanie

Użyj skrótu **Odinstaluj spolszczenie** z menu Start (albo „Aplikacje” w ustawieniach Windows). Dezinstalator przywraca oryginalny `bo2.exe` i usuwa pliki z napisami.
Gra musi być wtedy zamknięta. Oryginał możesz też przywrócić, sprawdzając integralność plików gry w kliencie GOG lub Steam.

## Wspieraj nasze projekty

Jeśli chcesz nas wesprzeć finansowo, [postaw nam kawę na Ko-fi](https://ko-fi.com/veritaware).

Aby dyskutować nad postępami prac i śledzić nasze przyszłe projekty, dołącz do nas na naszym [serwerze Discord](https://discord.gg/bJKCtJcaDg).

## Dla programistów i tłumaczy

Budowanie narzędzi, praca nad poprawką, czcionką i napisami: [docs/tools.md](docs/tools.md). Wskazówki dla asystentów AI: [CLAUDE.md](CLAUDE.md).

---

#[EN] Blood Omen 2 PL - subtitles patch + Polish localization

An unofficial patch that adds subtitles to the dialogue and cutscenes of *Legacy of Kain: Blood Omen 2* (PC version), by Grupa Polonizacyjna Nosgothica (the Nosgothica Polonization Group).
The goal is Polish subtitles.

The PC version shows no subtitles. Its engine does contain a complete caption system, but it is switched off and there is no caption text for it.
Our patch switches it on and supplies the text.

## Status: **in progress, no release date**

| Part | State |
|---|---|
| Showing captions in the game | works (verified in the Slums opening scene) |
| Installer | written, not yet tried on Windows |
| Polish letters (ą ć ę ł ń ś ź ż) in the game's font | in preparation |
| Polish subtitles | in preparation |

There is no installer to download yet. When there is, it will be in [Releases](https://github.com/Grupa-Polonizacyjna-Nosgothica/blood-omen-2-pl/releases).

## Installation

1. Close the game and its launcher.
2. Download `BO2-PL-Setup-<version>.exe` from [Releases](https://github.com/Grupa-Polonizacyjna-Nosgothica/blood-omen-2-pl/releases) and run it (administrator rights are needed because games are often in protected folders).
3. The installer finds the game by itself (GOG, and Steam). If it does not, select the main game folder, the one with `bo2.exe`.
4. Start the game. Subtitles appear at the bottom of the screen during dialogue.

The installer **does not contain game files**. It changes a few bytes of your own `bo2.exe` on your computer and copies the subtitle files into `data\texts` in the game folder.
Before changing anything it saves a backup, `bo2.exe.plbackup`, next to the game file.

**Supported game version:** the GOG version. The installer checks the game file and refuses to modify a different version. The Steam version has not been tested.

## After a game update or file verification

Verifying the game files in GOG Galaxy or Steam restores the original `bo2.exe` and removes the patch.
Run the **Apply the translation again** shortcut from the Start menu to put it back.

## Uninstalling

Use the **Uninstall the translation** shortcut in the Start menu (or "Apps" in the Windows settings). The uninstaller restores the original `bo2.exe` and removes the subtitle files.
The game must be closed. You can also restore the original by verifying the game files in your GOG or Steam client.

## Support our projects

If you want to support us financially, [buy us a coffee on Ko-fi](https://ko-fi.com/veritaware).

To discuss our progress and follow our future projects, join our [Discord server](https://discord.gg/bJKCtJcaDg).

## For developers and translators

Building the tools, working on the patch, the font and the subtitles: [docs/tols.md](docs/tools.md). Notes for AI assistants: [CLAUDE.md](CLAUDE.md).
