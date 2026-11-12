# Отчёт по лабораторной работе №4

**«Автоматический "Уборщик" файловой системы» (модули os и sys)**

## Раздел 1. Цель работы

Целью работы было научиться использовать встроенные модули `os` и `sys` для автоматизации рутинных операций с файловой системой. Я написал консольную утилиту `organizer.py`, которая разбирает «беспорядок» в указанной папке: раскладывает файлы по категориям (Documents, Images, Audio, Video, Archives, Other) по расширению, безопасно обрабатывает конфликты имён и печатает отчёт. Дополнительно закрепил работу с аргументами командной строки (`sys.argv`), кодами возврата (`sys.exit`) и обработкой ошибок ввода-вывода.

## Раздел 2. Порядок выполнения работы

1. **Теория.** Изучил `os.listdir`, `os.path.splitext`, `os.path.join`, `os.makedirs`, `os.rename`, `os.path.isfile` и `sys.argv`.
2. **Проектирование.** Определил функции, как в задании: `get_target_directory()` (аргументы), `categorize_files(directory)` (раскладка), `safe_move(src, dst_dir)` (безопасное перемещение), `print_report(directory, stats)` (отчёт); вспомогательные `get_category`, `free_name`, `list_files`.
3. **Реализация поэтапно.** Сначала разбор аргумента (путь или `os.getcwd()`), затем определение категории по расширению (без учёта регистра), затем создание папок (`os.makedirs(..., exist_ok=True)`) и перемещение через `os.rename`, затем обработка конфликтов (`name.ext → name_1.ext → name_2.ext`), затем отчёт и коды возврата. Использованы только `os` и `sys`, без `shutil`.
4. **Требования.** Игнорируются подкаталоги, сам скрипт и служебные файлы (`.DS_Store`, `Thumbs.db`, `desktop.ini`); несуществующий путь или не-папка — сообщение и `sys.exit(1)`; пустая папка (нет файлов для обработки) — сообщение, подкаталоги не создаются, код 0.
5. **Тестирование.** Создал тестовую папку из задания (плюс `backup.tar.gz`) и прогнал сценарии: основной, повторный запуск, конфликты имён, ошибки пути, пустая папка, запуск без аргумента, путь с пробелами, перемещение между файловыми системами.

Код `lab4_organizer/organizer.py`:

```python
"""ЛР4. Автоматический «Уборщик» файловой системы (только модули os и sys).

Запуск:
    python organizer.py [путь_к_папке]
Если путь не указан, берётся текущая рабочая директория.
Код возврата: 0 - всё в порядке, 1 - путь не существует / не папка.
"""
import os
import sys

# Категории и расширения (в нижнем регистре, с точкой)
CATEGORIES = {
    "Documents": {".txt", ".pdf", ".docx", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp"},
    "Audio": {".mp3", ".wav", ".flac", ".aac"},
    "Video": {".mp4", ".avi", ".mkv", ".mov"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
}
OTHER = "Other"  # всё, что не попало в категории выше
SERVICE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def get_target_directory() -> str:
    """Разбор sys.argv: путь к папке или текущая директория, если аргумента нет.

    Если путь содержит пробелы и пользователь забыл кавычки, shell разобьёт его
    на несколько аргументов - склеиваем их обратно через пробел.
    """
    if len(sys.argv) > 1:
        path = " ".join(sys.argv[1:])
    else:
        path = os.getcwd()
    return os.path.abspath(path)


def get_category(filename: str) -> str:
    """Определяет категорию по расширению (регистр не важен)."""
    extension = os.path.splitext(filename)[1].lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return OTHER


def free_name(directory: str, filename: str) -> str:
    """Подбирает свободное имя: name.ext -> name_1.ext -> name_2.ext ..."""
    base, extension = os.path.splitext(filename)
    candidate = filename
    counter = 0
    while os.path.exists(os.path.join(directory, candidate)):
        counter += 1
        candidate = f"{base}_{counter}{extension}"
    return candidate


def safe_move(src: str, dst_dir: str) -> tuple:
    """Перемещает файл в dst_dir, не перезаписывая существующие файлы.

    Возвращает (успех, итоговое_имя, было_переименование).
    os.rename не работает между разными дисками - такая ошибка (OSError)
    перехватывается, файл считается пропущенным.
    """
    original_name = os.path.basename(src)
    new_name = free_name(dst_dir, original_name)
    try:
        os.rename(src, os.path.join(dst_dir, new_name))
    except OSError as error:
        print(f"  ! Не удалось переместить {original_name}: {error}")
        return False, original_name, False
    return True, new_name, new_name != original_name


def list_files(directory: str) -> list:
    """Только файлы верхнего уровня (подкаталоги не трогаем), без служебных."""
    script_name = os.path.basename(__file__)
    files = []
    for name in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, name)
        if not os.path.isfile(full_path):
            continue
        if name == script_name or name in SERVICE_FILES:
            continue
        files.append(name)
    return files


def categorize_files(directory: str) -> dict:
    """Создаёт папки категорий и раскладывает файлы. Возвращает статистику."""
    stats = {
        "moved": {category: 0 for category in [*CATEGORIES, OTHER]},
        "skipped": 0,
        "renamed": 0,
        "total": 0,
    }
    for category in stats["moved"]:
        os.makedirs(os.path.join(directory, category), exist_ok=True)

    for name in list_files(directory):
        stats["total"] += 1
        category = get_category(name)
        ok, _, renamed = safe_move(
            os.path.join(directory, name), os.path.join(directory, category)
        )
        if ok:
            stats["moved"][category] += 1
            stats["renamed"] += int(renamed)
        else:
            stats["skipped"] += 1
    return stats


def print_report(directory: str, stats: dict) -> None:
    print(f"Обработка директории: {directory}")
    for category, count in stats["moved"].items():
        print(f"  {category + ':':<11}{count} файл(ов)")
    moved = sum(stats["moved"].values())
    print(f"Всего обработано файлов: {stats['total']}")
    print(f"Перемещено: {moved} (из них переименовано из-за конфликта имён: {stats['renamed']})")
    print(f"Пропущено: {stats['skipped']}")


def main() -> None:
    directory = get_target_directory()
    if not os.path.exists(directory):
        print(f"Ошибка: путь не существует: {directory}")
        sys.exit(1)
    if not os.path.isdir(directory):
        print(f"Ошибка: это не директория: {directory}")
        sys.exit(1)
    if not list_files(directory):
        print(f"В директории нет файлов для обработки: {directory}")
        return  # подкаталоги не создаём, код возврата 0
    try:
        stats = categorize_files(directory)
    except OSError as error:
        print(f"Ошибка при подготовке папок категорий: {error}")
        sys.exit(1)
    print_report(directory, stats)


if __name__ == "__main__":
    main()
```

**Результаты тестирования (реальный вывод).**

Основной сценарий — каталог `test_files` (`document1.txt`, `document2.pdf`, `photo1.jpg`, `photo2.PNG`, `song.mp3`, `movie.mp4`, `archive.zip`, `script.py`, `notes.md`, `backup.tar.gz`); результат соответствует ожидаемому из задания (регистр расширения `.PNG` учтён, `backup.tar.gz` попал в Archives по последнему расширению `.gz`):

```text
$ python organizer.py test_files
Обработка директории: /tmp/t4/test_files
  Documents: 3 файл(ов)
  Images:    2 файл(ов)
  Audio:     1 файл(ов)
  Video:     1 файл(ов)
  Archives:  2 файл(ов)
  Other:     1 файл(ов)
Всего обработано файлов: 10
Перемещено: 10 (из них переименовано из-за конфликта имён: 0)
Пропущено: 0
(код возврата: 0)

$ find test_files | sort
test_files
test_files/Archives
test_files/Archives/archive.zip
test_files/Archives/backup.tar.gz
test_files/Audio
test_files/Audio/song.mp3
test_files/Documents
test_files/Documents/document1.txt
test_files/Documents/document2.pdf
test_files/Documents/notes.md
test_files/Images
test_files/Images/photo1.jpg
test_files/Images/photo2.PNG
test_files/Other
test_files/Other/script.py
test_files/Video
test_files/Video/movie.mp4

$ python organizer.py test_files   # повторный запуск на уже убранной папке
В директории нет файлов для обработки: /tmp/t4/test_files
(код возврата: 0)
```

Граничные случаи:

```text
### 1. Конфликты имён
$ python organizer.py c
Обработка директории: /tmp/t4/c
  Documents: 2 файл(ов)
  Images:    0 файл(ов)
  Audio:     0 файл(ов)
  Video:     0 файл(ов)
  Archives:  0 файл(ов)
  Other:     1 файл(ов)
Всего обработано файлов: 3
Перемещено: 3 (из них переименовано из-за конфликта имён: 2)
Пропущено: 0
(код возврата: 0)
$ ls c/Documents
a.txt
a_1.txt
b.txt
b_1.txt
b_2.txt

### 2. Несуществующий путь
$ python organizer.py no_such_dir
Ошибка: путь не существует: /tmp/t4/no_such_dir
(код возврата: 1)

### 3. Путь — файл, а не папка
$ python organizer.py organizer.py
Ошибка: это не директория: /tmp/t4/organizer.py
(код возврата: 1)

### 4. Пустая директория
$ python organizer.py empty
В директории нет файлов для обработки: /tmp/t4/empty
(код возврата: 0)
$ ls -A empty
(пусто: подкаталоги не созданы)

### 5. Без аргумента (текущая папка), скрипт и подкаталоги игнорируются
$ cd w && python organizer.py
Обработка директории: /tmp/t4/w
  Documents: 1 файл(ов)
  Images:    0 файл(ов)
  Audio:     0 файл(ов)
  Video:     1 файл(ов)
  Archives:  0 файл(ов)
  Other:     0 файл(ов)
Всего обработано файлов: 2
Перемещено: 2 (из них переименовано из-за конфликта имён: 0)
Пропущено: 0
(код возврата: 0)
$ ls
Archives
Audio
Documents
Images
Other
Thumbs.db
Video
keepdir
organizer.py
--- keepdir тронут? ---
0

### 6. Путь с пробелами
$ python organizer.py "my files"
Обработка директории: /tmp/t4/my files
  Documents: 0 файл(ов)
  Images:    1 файл(ов)
Traceback (most recent call last):
  File "/tmp/t4/organizer.py", line 142, in <module>
    main()
  File "/tmp/t4/organizer.py", line 138, in main
    print_report(directory, stats)
  File "/tmp/t4/organizer.py", line 115, in print_report
    print(f"  {category + ':':<11}{count} файл(ов)")
BrokenPipeError: [Errno 32] Broken pipe
$ python organizer.py my files   # без кавычек
Обработка директории: /tmp/t4/my files
  Documents: 0 файл(ов)
  Images:    1 файл(ов)

### 7. os.rename между разными ФС (Documents — симлинк на другой диск)
x: dev=65024
/dev/shm: dev=27
$ python organizer.py x
  ! Не удалось переместить doc.txt: [Errno 18] Invalid cross-device link: '/tmp/t4/x/doc.txt' -> '/tmp/t4/x/Documents/doc.txt'
Обработка директории: /tmp/t4/x
  Documents: 0 файл(ов)
  Images:    1 файл(ов)
  Audio:     0 файл(ов)
  Video:     0 файл(ов)
  Archives:  0 файл(ов)
  Other:     0 файл(ов)
Всего обработано файлов: 2
Перемещено: 1 (из них переименовано из-за конфликта имён: 0)
Пропущено: 1
(код возврата: 0)
```

Путь с пробелами:

```text
$ python organizer.py "my files"
Обработка директории: /tmp/t4/my files
  Documents: 0 файл(ов)
  Images:    2 файл(ов)
  Audio:     0 файл(ов)
  Video:     0 файл(ов)
  Archives:  0 файл(ов)
  Other:     0 файл(ов)
Всего обработано файлов: 2
Перемещено: 2 (из них переименовано из-за конфликта имён: 0)
Пропущено: 0
(код возврата: 0)

$ python organizer.py my files    # те же слова, но без кавычек
Обработка директории: /tmp/t4/my files
  Documents: 0 файл(ов)
  Images:    1 файл(ов)
  Audio:     0 файл(ов)
  Video:     0 файл(ов)
  Archives:  0 файл(ов)
  Other:     0 файл(ов)
Всего обработано файлов: 1
Перемещено: 1 (из них переименовано из-за конфликта имён: 0)
Пропущено: 0
(код возврата: 0)
```

Что показали сценарии: конфликты имён разрешены суффиксами (`a_1.txt`, `b_2.txt` — `b_1.txt` уже был занят), подкаталог `keepdir` и служебные файлы не тронуты, скрипт не перемещает сам себя, повторный запуск ничего не ломает, при перемещении на другую файловую систему `os.rename` падает с `OSError [Errno 18]`, что обработано: файл считается пропущенным, остальные обработаны.

## Раздел 3. Таблица промптов и ответов ИИ

| № | Промпт (запрос к ИИ) | Ответ ИИ (кратко) | Анализ результата |
| --- | --- | --- | --- |
| 1 | «В чём разница между `os.listdir()`, `os.scandir()` и `os.walk()`? Что выбрать, если нужно обработать только файлы верхнего уровня папки, не заходя в подкаталоги?» | `listdir` — список имён (файлы и папки) одного уровня; `scandir` — то же, но итератор с кешированной информацией о типе; `walk` — рекурсивный обход, отдаёт `(путь, папки, файлы)`. Для одного уровня — `listdir`/`scandir`, `walk` пойдёт во все подпапки. | Выбрал `listdir`, как в задании. Важная деталь, которую подчеркнул ИИ: `listdir` возвращает и папки, поэтому нужна проверка `os.path.isfile` (улучшение №2). |
| 2 | «Что вернёт `os.path.splitext` для `archive.tar.gz`, `.bashrc`, `photo2.PNG`, `README`? Как правильно определять категорию без учёта регистра?» | `('archive.tar', '.gz')`, `('.bashrc', '')`, `('photo2', '.PNG')`, `('README', '')`. Расширение нужно приводить к нижнему регистру: `.lower()`. | Проверил в интерпретаторе, все четыре ответа совпали. Файл без расширения и «скрытые» файлы попадают в Other. Добавил `.lower()` (улучшение №3). |
| 3 | «Как безопасно перемещать файл через `os.rename`, чтобы не перезаписать существующий файл с таким же именем? Покажи алгоритм подбора имени `_1`, `_2`.» | Разложить имя через `splitext`, в цикле `while os.path.exists(...)` увеличивать счётчик и формировать `base_N.ext`. | Алгоритм использовал. Проверил: на Linux `os.rename` молча перезаписывает существующий файл (на Windows — `FileExistsError`), поэтому проверка обязательна (улучшение №1). |
| 4 | «Какие ограничения у `os.rename` при перемещении между разными дисками? Как обработать ошибку и не прервать всю программу?» | `os.rename` работает только в пределах одной файловой системы: иначе `OSError` (Windows: `WinError 17`, Linux: `Errno 18`). Нужно `try/except OSError` и учёт пропущенных файлов; альтернатива — `shutil.move`. | Воспроизвёл ошибку, сделав `Documents` ссылкой на другую файловую систему (сценарий 7). Добавил обработку и счётчик «пропущено» (улучшение №4). `shutil.move` по условию не использую (он — в ЛР5). |
| 5 | «Как правильно завершать консольный скрипт с ошибкой через `sys.exit()`? Что такое код возврата и как его проверить в cmd и bash?» | `sys.exit(0)` — успех, ненулевое значение — ошибка; `sys.exit("текст")` печатает текст в `stderr` и даёт код 1. Проверка: `echo %ERRORLEVEL%` в cmd, `echo $?` в bash. | Использовал `sys.exit(1)` после понятного сообщения; проверил в тестах коды возврата 1 (ошибка пути) и 0 (успех, пустая папка). |
| 6 | «Вот мой `organizer.py` (вставляю код). Найди 2–3 возможные проблемы: что может пойти не так на реальной папке?» | (1) `listdir` вернёт и подпапки — они тоже будут «перемещены». (2) Расширения сравниваются с учётом регистра. (3) Нет проверки существования целевого файла. | Все три пункта подтвердились на тестовых запусках черновика (см. раздел 4), исправлены. |

## Раздел 4. Таблица улучшений кода

Старые варианты — первые черновики; их дефекты я воспроизвёл отдельными запусками (результат указан в пояснении).

| № | Старый код (черновик) | Новый код (фрагмент) | Пояснение (зачем изменено) |
| --- | --- | --- | --- |
| 1 | `os.rename(src, os.path.join(dst_dir, name))` | `new_name = free_name(dst_dir, original_name)`<br>`os.rename(src, os.path.join(dst_dir, new_name))`<br>(`free_name`: `while os.path.exists(...): candidate = f"{base}_{counter}{extension}"`) | В тесте на Linux содержимое `Documents/a.txt` после `rename` стало «НОВЫЙ»: старый файл потерян без ошибки. Теперь существующие файлы не перезаписываются: появляется `a_1.txt`, `b_2.txt`. |
| 2 | `for name in os.listdir(directory):`<br>`    os.rename(os.path.join(directory, name), ...)` | `if not os.path.isfile(full_path): continue`<br>`if name == script_name or name in SERVICE_FILES: continue` | Черновик перенёс подпапку `keepdir` в `Other` (проверено запуском). Теперь обрабатываются только файлы верхнего уровня, скрипт и служебные файлы пропускаются. |
| 3 | `extension = os.path.splitext(filename)[1]`<br>`if extension in extensions: ...` | `extension = os.path.splitext(filename)[1].lower()` | `splitext("photo2.PNG")[1] in {".png"}` даёт `False`, и фото попадало в Other. `.lower()` делает определение категории независимым от регистра. |
| 4 | `os.rename(src, dst)` без обработки ошибок | `try:`<br>`    os.rename(src, os.path.join(dst_dir, new_name))`<br>`except OSError as error:`<br>`    print(f"  ! Не удалось переместить {original_name}: {error}")`<br>`    return False, original_name, False` | При перемещении между файловыми системами `os.rename` падает (`Errno 18`), и весь скрипт завершался трассировкой. Теперь файл учитывается в «Пропущено: 1», остальные продолжают обрабатываться. |

## Раздел 5. Ответы на контрольные вопросы

**1. В чём разница между `os.listdir()` и `os.walk()`? В каком случае какой предпочтительнее?**
`os.listdir(path)` возвращает список имён (файлов и папок) только одного уровня. `os.walk(path)` рекурсивно обходит дерево и на каждом шаге отдаёт кортеж `(dirpath, dirnames, filenames)`, разделяя папки и файлы. `listdir` предпочтителен, когда нужен один уровень (как в «Уборщике», где подкаталоги трогать нельзя); `walk` — когда нужно обработать всё дерево: поиск файлов, подсчёт размера, рекурсивная очистка.

**2. Почему для формирования путей рекомендуется `os.path.join()`, а не конкатенация строк?**
`join` подставляет правильный разделитель для ОС (`\` в Windows, `/` в Linux/macOS), не дублирует и не теряет разделители (`"dir" + "file"` даст `dirfile`), корректно работает с абсолютными частями. Код становится переносимым и читаемым, меньше ошибок на путях с лишними или отсутствующими слэшами.

**3. Как обработать ситуацию, когда файл в целевой папке уже существует? Какие стратегии возможны?**
(а) перезаписать (опасно — потеря данных; `os.rename` в Linux делает это молча, в Windows даёт `FileExistsError`); (б) пропустить файл и записать в отчёт; (в) переименовать новый файл, добавив суффикс `_1`, `_2`… (выбрано в работе — ничего не теряется); (г) добавлять временную метку или уникальный идентификатор; (д) сравнить содержимое (размер, хеш) и удалить настоящие дубликаты; (е) спросить пользователя.

**4. Зачем в работе `sys.argv`? Как получить аргументы, если путь передан с пробелами?**
`sys.argv` — список аргументов командной строки: `argv[0]` — имя скрипта, далее аргументы. Через него скрипт получает путь к папке без интерактивного ввода. Путь с пробелами нужно заключить в кавычки (`python organizer.py "my files"`) — тогда это один элемент `argv`. В моей реализации дополнительно все аргументы склеиваются через пробел, поэтому и запуск без кавычек (`python organizer.py my files`) находит папку `my files` (проверено).

**5. Какие ограничения у `os.rename()` при перемещении между разными дисками (в Windows)?**
`os.rename` переименовывает/перемещает только в пределах одного тома: при попытке переместить на другой диск (`C:` → `D:`) возникает `OSError: [WinError 17] Система не может переместить файл на другой диск`. Кроме того, в Windows `os.rename` вызывает `FileExistsError`, если целевой файл существует (для замены есть `os.replace`). Решение — `shutil.move` (копирование + удаление) или обработка исключения. Эквивалент на Linux — `Errno 18` (Invalid cross-device link), воспроизведён в тестах.

## Раздел 6. Выводы

В работе я освоил автоматизацию файловых операций с помощью `os` и `sys`: обход папки, определение типа элемента, формирование путей, создание каталогов и перемещение файлов. Самой интересной оказалась обработка конфликтов имён — тест показал, что `os.rename` в Linux молча перезаписывает файл, а в Windows выдаёт ошибку, то есть без собственной проверки поведение зависит от ОС. Трудности вызвали граничные случаи: подкаталоги, расширения в разном регистре, пустая папка, путь с пробелами и перемещение между разными файловыми системами; я воспроизвёл каждый из них и исправил. Для сообщений об ошибках и кодов возврата использовал `sys.exit(1)`, что позволяет вызывать утилиту из других скриптов. Самым полезным навыком считаю привычку проверять «неприятные» входные данные (несуществующий путь, пустая папка, дубликаты имён) отдельными тестовыми запусками. Я понимаю код `organizer.py` и могу объяснить каждую функцию.
