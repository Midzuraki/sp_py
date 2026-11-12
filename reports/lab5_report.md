# Отчёт по лабораторной работе №5

**«Тот же "Уборщик", но на pathlib + shutil + argparse»**

## Раздел 1. Цель работы

Целью работы было переписать «Уборщик» из ЛР4, заменив низкоуровневые `os` и `sys` на современные инструменты: `pathlib` для путей, `shutil.move` для перемещения и `argparse` для аргументов командной строки. Я сохранил ту же логику (категории, конфликты имён, отчёт), добавил режимы `--dry-run` и `--verbose`, обработку составных расширений и пропуск служебных файлов. Главный результат — понимание, как та же задача решается идиоматичнее и какие компромиссы при этом возникают.

## Раздел 2. Порядок выполнения работы

1. Взял за основу структуру из ЛР4 и спроектировал функции по заданию: `parse_args()`, `get_category(suffix)`, `resolve_conflict(dst)`, `organize(directory, dry_run, verbose)`, `print_report(...)`; добавил `collect_files` и `plural_files` (склонение «файл/файла/файлов»).
2. Заменил `sys.argv` на `argparse.ArgumentParser`: необязательный позиционный `directory` (по умолчанию `.`), флаги `--dry-run` и `--verbose`.
3. Заменил `os.path.*` и `os.listdir` на `Path`, оператор `/`, `Path.iterdir()`, `Path.is_file()`, `Path.suffix`, `Path.mkdir(parents=True, exist_ok=True)`.
4. Конфликты имён реализовал через `Path.with_stem` (Python 3.9+): `notes.md → notes_1.md → notes_2.md`.
5. Перемещение — `shutil.move` (с объяснением в комментариях, почему не `Path.rename`).
6. Пропускаю сам скрипт (`Path(__file__).name`) и служебные файлы (`.DS_Store`, `Thumbs.db`, `desktop.ini`, без учёта регистра).
7. Протестировал: `--dry-run`, `--verbose`, запуск без аргументов, несуществующий путь, неизвестный флаг, `--help`, существующий `Documents` с конфликтами, пустая папка, перемещение между файловыми системами, символические и жёсткие ссылки.

Код `lab5_organizer_pathlib/organizer_pathlib.py`:

```python
"""ЛР5. «Уборщик» на pathlib + shutil + argparse (та же логика, что в ЛР4).

Запуск:
    python organizer_pathlib.py [directory] [--dry-run] [--verbose]
"""
import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

CATEGORIES: Dict[str, set] = {
    "Documents": {".txt", ".pdf", ".docx", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp"},
    "Audio": {".mp3", ".wav", ".flac", ".aac"},
    "Video": {".mp4", ".avi", ".mkv", ".mov"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
}
OTHER = "Other"
SERVICE_FILES = {".ds_store", "thumbs.db", "desktop.ini"}  # сравниваем в нижнем регистре


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """argparse вместо sys.argv: автоматические --help, проверка аргументов, usage."""
    parser = argparse.ArgumentParser(
        description="Раскладывает файлы папки по категориям (Documents, Images, ...)."
    )
    parser.add_argument(
        "directory",
        nargs="?",  # необязательный позиционный аргумент
        default=".",  # по умолчанию - текущая директория
        type=Path,
        help="папка для уборки (по умолчанию - текущая)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="только показать, что будет перемещено, ничего не менять",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="подробный вывод по каждому файлу"
    )
    return parser.parse_args(argv)


def get_category(suffix: str) -> str:
    """Категория по расширению (с точкой, регистр не важен)."""
    suffix = suffix.lower()
    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category
    return OTHER


def resolve_conflict(dst: Path) -> Path:
    """Подбирает свободное имя через Path.with_stem: notes.md -> notes_1.md -> ..."""
    if not dst.exists():
        return dst
    counter = 1
    candidate = dst.with_stem(f"{dst.stem}_{counter}")  # with_stem: Python 3.9+
    while candidate.exists():
        counter += 1
        candidate = dst.with_stem(f"{dst.stem}_{counter}")
    return candidate


def plural_files(n: int) -> str:
    """1 файл, 2 файла, 5 файлов (русские окончания)."""
    if n % 10 == 1 and n % 100 != 11:
        word = "файл"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        word = "файла"
    else:
        word = "файлов"
    return f"{n} {word}"


def collect_files(directory: Path) -> List[Path]:
    """Файлы верхнего уровня без самого скрипта и служебных файлов."""
    script_name = Path(__file__).name
    return sorted(
        item
        for item in directory.iterdir()
        if item.is_file()  # is_file() вместо os.path.isfile
        and item.name != script_name
        and item.name.lower() not in SERVICE_FILES
    )


def organize(directory: Path, dry_run: bool = False, verbose: bool = False) -> Dict:
    """Раскладывает файлы по категориям. Возвращает статистику."""
    stats: Dict = {
        "moved": {category: 0 for category in [*CATEGORIES, OTHER]},
        "skipped": 0,
        "renamed": 0,
    }
    files = collect_files(directory)
    if not files:
        stats["empty"] = True
        return stats

    if not dry_run:
        for category in stats["moved"]:
            # parents=True создаёт промежуточные папки, exist_ok=True не падает,
            # если папка уже есть (например, остался Documents с прошлого запуска)
            (directory / category).mkdir(parents=True, exist_ok=True)

    for file in files:
        # Path.suffix - ТОЛЬКО последний суффикс: archive.tar.gz -> ".gz" (Archives),
        # photo.jpeg -> ".jpeg" (Images). Path.suffixes дал бы [".tar", ".gz"].
        category = get_category(file.suffix)
        target = resolve_conflict(directory / category / file.name)
        conflict = target.name != file.name
        relative = f"{category}/{target.name}"

        if dry_run:
            print(f"[DRY-RUN] {file.name:<16} -> {relative}")
            stats["moved"][category] += 1
            stats["renamed"] += int(conflict)
            continue

        try:
            # shutil.move предпочтительнее Path.rename(): Path.rename - обёртка над
            # os.rename и падает с OSError между разными дисками/файловыми системами,
            # а shutil.move в этом случае сам копирует файл и удаляет оригинал.
            shutil.move(str(file), str(target))
        except (OSError, shutil.Error) as error:
            print(f"Ошибка:     {file.name} -> {relative} ({error})")
            stats["skipped"] += 1
            continue

        stats["moved"][category] += 1
        stats["renamed"] += int(conflict)
        if verbose:
            if conflict:
                print(f"Конфликт:   {file.name} -> {relative} (переименовано)")
            else:
                print(f"Перемещено: {file.name} -> {relative}")
    return stats


def print_report(directory: Path, stats: Dict, dry_run: bool) -> None:
    if dry_run:
        print("Ничего не изменено (режим dry-run).")
        return
    print(f"Обработка директории: {directory}")
    for category, count in stats["moved"].items():
        print(f"  {category + ':':<10} {plural_files(count)}")
    print(f"Итого перемещено: {sum(stats['moved'].values())}")
    if stats["renamed"]:
        print(f"Из них переименовано из-за конфликта имён: {stats['renamed']}")
    print(f"Пропущено: {stats['skipped']}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    directory: Path = args.directory.resolve()
    if not directory.exists():
        print(f"Ошибка: путь не существует: {directory}", file=sys.stderr)
        return 1
    if not directory.is_dir():
        print(f"Ошибка: это не директория: {directory}", file=sys.stderr)
        return 1

    stats = organize(directory, dry_run=args.dry_run, verbose=args.verbose)
    if stats.get("empty"):
        print(f"В директории нет файлов для обработки: {directory}")
        return 0
    print_report(directory, stats, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Результаты (реальный вывод).** Основные режимы на папке из задания (плюс `backup.tar.gz` и `photo.jpeg`):

```text
$ python organizer_pathlib.py test_files --dry-run
[DRY-RUN] archive.zip      -> Archives/archive.zip
[DRY-RUN] backup.tar.gz    -> Archives/backup.tar.gz
[DRY-RUN] document1.txt    -> Documents/document1.txt
[DRY-RUN] document2.pdf    -> Documents/document2.pdf
[DRY-RUN] movie.mp4        -> Video/movie.mp4
[DRY-RUN] notes.md         -> Documents/notes.md
[DRY-RUN] photo.jpeg       -> Images/photo.jpeg
[DRY-RUN] photo1.jpg       -> Images/photo1.jpg
[DRY-RUN] photo2.PNG       -> Images/photo2.PNG
[DRY-RUN] script.py        -> Other/script.py
[DRY-RUN] song.mp3         -> Audio/song.mp3
Ничего не изменено (режим dry-run).
(код: 0)
$ ls test_files
archive.zip
backup.tar.gz
document1.txt
document2.pdf
movie.mp4
notes.md
photo.jpeg
photo1.jpg
photo2.PNG
script.py
song.mp3

$ python organizer_pathlib.py test_files --verbose
Перемещено: archive.zip -> Archives/archive.zip
Перемещено: backup.tar.gz -> Archives/backup.tar.gz
Перемещено: document1.txt -> Documents/document1.txt
Перемещено: document2.pdf -> Documents/document2.pdf
Перемещено: movie.mp4 -> Video/movie.mp4
Перемещено: notes.md -> Documents/notes.md
Перемещено: photo.jpeg -> Images/photo.jpeg
Перемещено: photo1.jpg -> Images/photo1.jpg
Перемещено: photo2.PNG -> Images/photo2.PNG
Перемещено: script.py -> Other/script.py
Перемещено: song.mp3 -> Audio/song.mp3
Обработка директории: /tmp/t5/test_files
  Documents: 3 файла
  Images:    3 файла
  Audio:     1 файл
  Video:     1 файл
  Archives:  2 файла
  Other:     1 файл
Итого перемещено: 11
Пропущено: 0
(код: 0)
```

Граничные случаи и демонстрации:

```text
### 1. Запуск без аргументов (текущая папка = w), скрипт игнорируется
$ cd w && python organizer_pathlib.py
Обработка директории: /tmp/t5/w
  Documents: 1 файл
  Images:    0 файлов
  Audio:     1 файл
  Video:     0 файлов
  Archives:  0 файлов
  Other:     0 файлов
Итого перемещено: 2
Пропущено: 0
$ ls -A
.DS_Store
Archives
Audio
Documents
Images
Other
Thumbs.db
Video
organizer_pathlib.py

### 2. Несуществующий путь
$ python organizer_pathlib.py no_such
Ошибка: путь не существует: /tmp/t5/no_such
(код: 1)

### 3. Лишний/неизвестный флаг и --help
$ python organizer_pathlib.py --bad
usage: organizer_pathlib.py [-h] [--dry-run] [--verbose] [directory]
organizer_pathlib.py: error: unrecognized arguments: --bad
(код: 2)
$ python organizer_pathlib.py --help
usage: organizer_pathlib.py [-h] [--dry-run] [--verbose] [directory]

Раскладывает файлы папки по категориям (Documents, Images, ...).

positional arguments:
  directory   папка для уборки (по умолчанию - текущая)

options:
  -h, --help  show this help message and exit
  --dry-run   только показать, что будет перемещено, ничего не менять
  --verbose   подробный вывод по каждому файлу

### 4. Папка Documents уже существует и содержит файлы; конфликт имён
$ python organizer_pathlib.py c --verbose
Конфликт:   notes.md -> Documents/notes_2.md (переименовано)
Перемещено: z.docx -> Documents/z.docx
Обработка директории: /tmp/t5/c
  Documents: 2 файла
  Images:    0 файлов
  Audio:     0 файлов
  Video:     0 файлов
  Archives:  0 файлов
  Other:     0 файлов
Итого перемещено: 2
Из них переименовано из-за конфликта имён: 1
Пропущено: 0
$ ls c/Documents
notes.md
notes_1.md
notes_2.md
z.docx

### 5. Пустая папка
$ python organizer_pathlib.py e
В директории нет файлов для обработки: /tmp/t5/e
(код: 0)

### 6. Documents — симлинк на другую ФС: shutil.move справляется
$ python organizer_pathlib.py x --verbose
Перемещено: doc.txt -> Documents/doc.txt
Перемещено: pic.png -> Images/pic.png
Обработка директории: /tmp/t5/x
  Documents: 1 файл
  Images:    1 файл
  Audio:     0 файлов
  Video:     0 файлов
  Archives:  0 файлов
  Other:     0 файлов
Итого перемещено: 2
Пропущено: 0
$ ls /dev/shm/other_fs_docs
doc.txt

### 7. Path.suffix vs Path.suffixes
backup.tar.gz      suffix='.gz'    suffixes=['.tar', '.gz']
photo.jpeg         suffix='.jpeg'  suffixes=['.jpeg']
archive.zip        suffix='.zip'   suffixes=['.zip']
report.final.PDF   suffix='.PDF'   suffixes=['.final', '.PDF']
.bashrc            suffix=''       suffixes=[]

### 8. Path.rename vs shutil.move между разными ФС
$ python demo_rename_vs_move.py
Источник : /tmp
Назначение: /dev/shm

Path.rename : OSError -> [Errno 18] Invalid cross-device link: '/tmp/demo_Path.txt' -> '/dev/shm/demo_Path.txt'
shutil.move : OK, файл теперь в /dev/shm/demo_shutil.txt
```

Символические и жёсткие ссылки:

```text
$ ls -li
681228 lrwxrwxrwx 1 root root   18 Nov 11 23:25 broken.png -> missing_target.txt
681234 drwxr-xr-x 2 root root 4096 Nov 11 23:25 fs
681094 -rw-r--r-- 2 root root    5 Nov 11 23:25 hard.txt
681113 lrwxrwxrwx 1 root root    8 Nov 11 23:25 link.txt -> real.txt
681250 -rw-r--r-- 1 root root 7075 Nov 11 23:25 organizer_pathlib.py
681094 -rw-r--r-- 2 root root    5 Nov 11 23:25 real.txt
Перемещено: hard.txt -> Documents/hard.txt
Перемещено: link.txt -> Documents/link.txt
Перемещено: real.txt -> Documents/real.txt
Обработка директории: /tmp/sl
  Documents: 3 файла
  Images:    0 файлов
  Audio:     0 файлов
  Video:     0 файлов
  Archives:  0 файлов
  Other:     0 файлов
Итого перемещено: 3
Пропущено: 0

$ ls -liR Documents Images 2>&1 | head
total 8
681094 -rw-r--r-- 2 root root 5 Nov 11 23:25 hard.txt
681113 lrwxrwxrwx 1 root root 8 Nov 11 23:25 link.txt -> real.txt
681094 -rw-r--r-- 2 root root 5 Nov 11 23:25 real.txt
broken.png на месте? ->
lrwxrwxrwx 1 root root 18 Nov 11 23:25 broken.png -> missing_target.txt
```

### Что нужно показать при сдаче (раздел 7 задания)

**Сравнение двух реализаций.**

| Аспект | `organizer.py` (os + sys) | `organizer_pathlib.py` (pathlib + shutil + argparse) |
| --- | --- | --- |
| Размер (строки кода без пустых и комментариев) | ~118 | ~141 (больше за счёт `--dry-run`, `--verbose`, склонения, справки) |
| Пути | `os.path.join(dir, cat, name)` | `directory / category / name` — короче и читаемее |
| Список файлов | `os.listdir` + `os.path.isfile` (строки) | `iterdir()` + `is_file()` (объекты `Path` с методами) |
| Расширение | `os.path.splitext(name)[1]` | `file.suffix` |
| Аргументы | `sys.argv`, всё вручную | `argparse`: `--help`, usage, проверка флагов, значения по умолчанию |
| Перемещение | `os.rename` — не работает между дисками | `shutil.move` — сам копирует и удаляет, если `rename` невозможен |
| Предсказуемость | Простая и очевидная операция | `shutil.move` может копировать (дольше, теряет жёсткие ссылки), при существующем файле может перезаписать — защищает `resolve_conflict` |
| Скорость | Минимальные накладные расходы | Немного медленнее: создание объектов `Path`, `shutil.move` при копировании; для сотен файлов разница не заметна |
| Кроссплатформенность | Разделители вручную через `join` | `Path` сам подбирает правила Windows/POSIX |

**Разница `Path.rename()` и `shutil.move()`.** Запуск `python demo_rename_vs_move.py` (источник `/tmp`, назначение `/dev/shm` — другая файловая система):

```text
Path.rename : OSError -> [Errno 18] Invalid cross-device link: '/tmp/demo_Path.txt' -> '/dev/shm/demo_Path.txt'
shutil.move : OK, файл теперь в /dev/shm/demo_shutil.txt
```

`Path.rename` — обёртка над `os.rename` и не умеет работать между томами; `shutil.move` в этом случае автоматически выполняет копирование и удаление. Поэтому в сценарии, где пользователь может раскладывать файлы на другой диск, выбран `shutil.move` (сценарий 6: `Documents` — ссылка на другую файловую систему, файл перемещён успешно).

**Поведение `Path.mkdir(exist_ok=True)`.** Если папка уже есть, исключение не возникает, содержимое не трогается. `os.makedirs` без `exist_ok=True` в этой ситуации выбросит `FileExistsError` — повторный запуск скрипта на уже убранной папке падал бы. `exist_ok=True` делает операцию идемпотентной и устраняет гонку «проверил — создал» (папку могли создать между проверкой и созданием). При этом, если на месте папки лежит *файл* с таким именем, ошибка всё равно будет — это правильно.

**Работа с `argparse`** (запуск без аргументов — обработка текущей папки; несуществующий путь — сообщение и код 1; `--dry-run` — только показ; неизвестный флаг — usage и код 2; `--help` — автоматическая справка): всё показано в выводе выше (сценарии 1, 2, 3 и первый блок).

**Составные расширения.** `Path("backup.tar.gz").suffix == ".gz"`, `suffixes == [".tar", ".gz"]`. Файл `backup.tar.gz` попадает в **Archives**, потому что используется последний суффикс `.gz`, а `.gz` есть в списке архивов; `photo.jpeg` — в **Images** (`.jpeg`). Это поведение описано в комментарии в коде. Если бы использовался `suffixes`, пришлось бы отдельно решать, что делать с `report.final.PDF` (`['.final', '.PDF']`).

## Раздел 3. Таблица промптов и ответов ИИ

| № | Промпт (запрос к ИИ) | Ответ ИИ (кратко) | Анализ результата |
| --- | --- | --- | --- |
| 1 | «Чем `Path.rename()` отличается от `shutil.move()`? Покажи, на каком сценарии `Path.rename` падает.» | `Path.rename` вызывает `os.rename`, который работает в пределах одной файловой системы; при переносе на другой диск — `OSError`. `shutil.move` при невозможности `rename` копирует и удаляет оригинал. | Воспроизвёл разницу отдельным скриптом `demo_rename_vs_move.py` (вывод выше). Выбрал `shutil.move`. |
| 2 | «Как в `argparse` сделать необязательный позиционный аргумент со значением по умолчанию и флаги `--dry-run`, `--verbose`, которые не требуют значения?» | `add_argument("directory", nargs="?", default=".")` и `add_argument("--dry-run", action="store_true")`. | Использовал; добавил `type=Path`, чтобы сразу получать объект `Path`. Заметил: `--dry-run` доступен в коде как `args.dry_run` (дефис превращается в подчёркивание). |
| 3 | «Как подобрать свободное имя файла через `Path.with_stem`? С какой версии Python он доступен и что делать в более старых версиях?» | `dst.with_stem(f"{dst.stem}_{n}")`, метод появился в Python 3.9; ранее — `dst.with_name(f"{dst.stem}_{n}{dst.suffix}")`. | В `pyproject` других работ у меня `requires-python >= 3.9`, поэтому `with_stem` допустим. Проверил на `notes.md` при существующих `notes.md` и `notes_1.md` → получилось `notes_2.md`. |
| 4 | «Что вернёт `Path("backup.tar.gz").suffix` и `.suffixes`? Как лучше определять категорию для составных расширений?» | `.suffix == ".gz"`, `.suffixes == [".tar", ".gz"]`. Для простой категоризации достаточно последнего суффикса; `suffixes` нужен, если `.tar.gz` и `.gz` обрабатываются по-разному. | Оставил `suffix`, как требует задание, и описал поведение в комментариях. Проверил на пяти именах (см. вывод, сценарий 7). |
| 5 | «Как реализовать режим `--dry-run`, чтобы ничего не создавалось и не перемещалось, но вывод показывал, что именно произойдёт?» | Выполнять тот же цикл, но вместо `mkdir` и `move` печатать `[DRY-RUN] ...`; конфликты разрешать так же, но без изменений на диске. | Реализовал. Проверил, что после `--dry-run` в папке ничего не изменилось (`ls`) и нет созданных папок категорий. |
| 6 | «Что делает `shutil.move` с символическими и жёсткими ссылками? Какие подводные камни?» | В пределах одной ФС — `os.rename`: ссылка переносится как есть, жёсткая ссылка остаётся прежним inode. Между ФС: для symlink создаётся новая ссылка на ту же цель, для файла — копия (связь жёсткой ссылки теряется). Если целевой файл уже есть, `move` может его перезаписать. | Проверил на реальном запуске (inode у `hard.txt` и `real.txt` остался общим, symlink `link.txt` перенесён как ссылка, битая ссылка `broken.png` пропущена, так как `is_file()` для неё `False`). Защиту от перезаписи обеспечивает `resolve_conflict`. |

## Раздел 4. Таблица улучшений кода

В этой работе «старый код» — реальный код из ЛР4 (`organizer.py`), «новый» — из `organizer_pathlib.py`.

| № | Старый код (ЛР4, os + sys) | Новый код (ЛР5, pathlib + shutil + argparse) | Пояснение (зачем изменено) |
| --- | --- | --- | --- |
| 1 | `path = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else os.getcwd()` | `parser.add_argument("directory", nargs="?", default=".", type=Path)`<br>`parser.add_argument("--dry-run", action="store_true")`<br>`parser.add_argument("--verbose", action="store_true")` | `argparse` даёт `--help`, сообщения об ошибках в аргументах (`unrecognized arguments`, код 2), значения по умолчанию и флаги без ручного разбора `sys.argv`; скрипт легко расширять новыми опциями. |
| 2 | `ok, _, renamed = safe_move(os.path.join(directory, name), os.path.join(directory, category))`<br>(внутри — `os.rename`) | `shutil.move(str(file), str(target))` | `os.rename` падает при переносе между файловыми системами (проверено); `shutil.move` в этом случае копирует и удаляет оригинал, и сценарий с `Documents` на другом диске выполняется успешно. |
| 3 | `base, extension = os.path.splitext(filename)`<br>`while os.path.exists(os.path.join(directory, candidate)):`<br>`    candidate = f"{base}_{counter}{extension}"` | `candidate = dst.with_stem(f"{dst.stem}_{counter}")`<br>`while candidate.exists(): ...` | Имя и расширение не нужно разбирать вручную: `with_stem` меняет только имя и сохраняет суффикс; код короче и работает с объектами `Path`. |
| 4 | (в ЛР4 перед перемещением всегда создавались папки категорий, режима «посмотреть» не было) | `if not dry_run:`<br>`    for category in stats["moved"]:`<br>`        (directory / category).mkdir(parents=True, exist_ok=True)`<br>`...`<br>`if dry_run: print(f"[DRY-RUN] {file.name:<16} -> {relative}")` | `--dry-run` позволяет безопасно проверить результат до изменения файлов; `mkdir(exist_ok=True)` делает повторные запуски идемпотентными. |

## Раздел 5. Ответы на контрольные вопросы

**1. Чем `Path.rename()` отличается от `shutil.move()` и в каких случаях каждый предпочтителен?**
`Path.rename()` — тонкая обёртка над `os.rename`: быстрая атомарная операция, но только в пределах одной файловой системы (иначе `OSError`); в Windows не заменяет существующий файл (`FileExistsError`). `shutil.move()` сначала пробует `rename`, а если не получилось — копирует и удаляет оригинал; работает между дисками и с каталогами, но медленнее и может перезаписать существующий файл. `rename` предпочтителен внутри одного тома (атомарность, скорость), `move` — когда источник и приёмник могут быть на разных файловых системах (как в «Уборщике»).

**2. Что произойдёт, если запустить скрипт на папке, где уже есть подкаталог `Documents` с файлами? Как поведёт себя `Path.mkdir(exist_ok=True)`?**
`mkdir(parents=True, exist_ok=True)` не вызовет ошибку и не тронет существующее содержимое. Подкаталоги итерация `collect_files` пропускает (`is_file()` для них `False`). Файлы с совпадающими именами получат суффиксы (в тесте `notes.md` стал `notes_2.md`, потому что `notes.md` и `notes_1.md` уже были). Если же `Documents` окажется *файлом*, `mkdir` выдаст `FileExistsError`.

**3. Как `pathlib` позволяет избавиться от ручной конкатенации путей и почему это важно для кроссплатформенности?**
Оператор `/` объединяет части пути (`directory / category / name`), а `Path` сам использует правильный разделитель и правила регистра Windows или POSIX (`PureWindowsPath`/`PurePosixPath`). Не нужно вручную подставлять `\` или `/`, думать о лишних слэшах и склейке строк; один и тот же код работает на любой ОС, а у пути есть удобные свойства (`name`, `stem`, `suffix`, `parent`).

**4. В чём разница между `Path.suffix` и `Path.suffixes`? Приведите пример, где это существенно.**
`suffix` — последний суффикс (`.gz`), `suffixes` — список всех (`['.tar', '.gz']`). Различие важно для `backup.tar.gz` (архив tar, сжатый gzip), `data.v1.2.csv` (`suffixes == ['.v1', '.2', '.csv']`, `suffix == '.csv'`) и `report.final.PDF`. В «Уборщике» используется `suffix`, поэтому `backup.tar.gz` определяется как `.gz` и попадает в Archives.

**5. Почему в современном Python рекомендуется `argparse` вместо `sys.argv`? Какие преимущества это даёт при развитии скрипта?**
`argparse` автоматически разбирает позиционные и именованные аргументы, типы, значения по умолчанию, флаги, генерирует `--help`/usage и сообщения об ошибках с кодом 2, поддерживает взаимоисключающие группы и подкоманды. С `sys.argv` всё это приходится писать вручную, а при добавлении каждого нового параметра код разрастается и ломается. Скрипт на `argparse` самодокументирован и проще поддерживается.

**6. Какие ограничения у `shutil.move()` при работе с символическими и жёсткими ссылками?**
В пределах одной ФС `move` использует `rename`, поэтому и симлинк, и жёсткая ссылка переносятся без изменений (inode сохраняется — в тесте у `hard.txt` и `real.txt` общий inode). Между разными ФС для симлинка создаётся новая ссылка на ту же цель (содержимое цели не копируется; относительная ссылка может «сломаться», если цель осталась в другом месте), а для файла делается копия, и связь жёсткой ссылки теряется (получаются независимые файлы). Симлинк на папку перемещается как ссылка, а не как каталог. В нашем скрипте `is_file()` следует по ссылке, поэтому битая ссылка пропускается, а ссылка на файл перемещается как ссылка.

## Раздел 6. Выводы

Переписав «Уборщик» на `pathlib`, `shutil` и `argparse`, я увидел, что код стал читаемее: пути собираются оператором `/`, расширение и имя берутся свойствами, а аргументы разбираются декларативно, с готовой справкой и проверкой флагов. Новые требования — `--dry-run`, `--verbose`, составные расширения — реализовались проще благодаря объектной модели `Path`. Для перемещения выбрал `shutil.move`, так как `Path.rename` не работает между файловыми системами: это я проверил отдельным скриптом. Недостаток — чуть больший размер программы и менее очевидное поведение `shutil.move` (копирование, возможная перезапись), которое нужно компенсировать проверкой конфликтов. Трудность вызвали ссылки (жёсткие и символические), для которых я проверил реальное поведение. Самым полезным навыком считаю режим `--dry-run`: он позволяет безопасно тестировать скрипты, меняющие файлы. Я понимаю код `organizer_pathlib.py` и могу объяснить каждую функцию.
