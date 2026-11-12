# Отчёт по лабораторной работе №6

**«Запуск внешних программ. Модуль subprocess» (менеджер задач runner.py)**

## Раздел 1. Цель работы

Целью работы было научиться запускать внешние программы из Python через модуль `subprocess` и написать консольный «Менеджер задач» `runner.py`: он последовательно или параллельно запускает команды, собирает `stdout` и `stderr`, обрабатывает коды возврата, таймауты и отсутствующие программы и формирует отчёт в консоль и в файл `report.txt`. Отдельно нужно было разобраться, почему `os.system` небезопасен, чем `subprocess.run()` отличается от `Popen`, и как учитывать особенности Windows (встроенные команды `cmd.exe`, кодировки CP866/UTF-8).

## Раздел 2. Порядок выполнения работы

1. **Подготовка.** Папка `runner_project/` с файлом `runner.py`; в Windows — `chcp 65001` для UTF-8 в консоли и `python --version` для проверки интерпретатора.
2. **Теория.** `subprocess.run` (параметры `capture_output`, `text`, `encoding`, `timeout`, `check`), исключения `TimeoutExpired`, `CalledProcessError`, `FileNotFoundError`, особенности Windows (`cmd /c`, CP866, `shutil.which`).
3. **Проектирование функций** (как в задании): `parse_args(argv)`, `split_command(cmd_str)`, `pick_encoding(cmd)`, `run_command(cmd, timeout=10)`, `run_parallel(cmds, timeout=10)`, `format_report(results, ...)`, `save_report(text, path)`; дополнительно `console_encoding`, `parse_codepage`.
4. **Реализация поэтапно:** разбор аргументов (`--slow` первым аргументом, команда по умолчанию `python --version` с предупреждением) → одна команда через `subprocess.run([...])` с перехватом вывода → обработка исключений (не найдена, таймаут 10 с, ненулевой код через `check=True`) → параллельный режим через `Popen` → отчёт и сохранение в UTF-8.
5. **Ограничения выполнены:** только `subprocess`, `sys`, `time`, `os`, `shutil`; нет `os.system`, `os.popen`, `shell=True`; строка команды разбирается вручную по пробелам в список (`"cmd /c del /q *"` → `['cmd', '/c', 'del', '/q', '*']`); `FileNotFoundError` и таймаут не прерывают работу; код выхода 0, если успешна хотя бы одна команда, иначе 1.
6. **Кодировка:** для системных утилит Windows (`cmd`, `findstr`, `ping`, `where`, `dir`, `type`, `timeout`) вывод читается в кодировке консоли — по умолчанию CP866; для остального — UTF-8; `errors="replace"` защищает от битых байтов.

Код `lab6_runner/runner.py`:

```python
"""ЛР6. Менеджер запуска внешних команд (модуль subprocess, ориентирован на Windows).

Примеры:
    python runner.py "python --version" "ping -n 2 8.8.8.8"
    python runner.py --slow "ping -n 2 8.8.8.8" "ping -n 2 1.1.1.1" "python --version"
Без аргументов запускается `python --version`.
Код возврата: 0, если хотя бы одна команда успешна, иначе 1.
Только стандартные модули: subprocess, sys, time, os, shutil. Без shell=True и os.system.
"""
import os
import shutil
import subprocess
import sys
import time

TIMEOUT = 10  # секунд на каждую команду
REPORT_FILE = "report.txt"
PREVIEW_LEN = 200  # сколько символов stdout/stderr показывать в консоли
# Системные утилиты Windows пишут в консольной кодировке CP866
SYSTEM_UTILS = {"cmd", "findstr", "ping", "where", "dir", "type", "timeout"}

# Статусы
OK, ERROR, TIMED_OUT, NOT_FOUND = "успех", "ошибка", "таймаут", "не найдена"


def parse_args(argv):
    """Возвращает (список_команд, slow). Первым аргументом может быть --slow."""
    args = list(argv)
    slow = False
    if args and args[0] == "--slow":
        slow = True
        args = args[1:]
    if not args:
        print("Предупреждение: команды не переданы, используется `python --version`")
        args = ["python --version"]
    return args, slow


def split_command(cmd_str):
    """Ручной разбор по пробелам: строка -> список аргументов (БЕЗ шелла).

    "cmd /c del /q *" -> ["cmd", "/c", "del", "/q", "*"]. Метасимволы &, |, > остаются
    обычными аргументами и не интерпретируются: список уходит прямо в CreateProcess/exec.
    Ограничение: аргументы с пробелами внутри кавычек не поддерживаются.
    """
    return cmd_str.split()


def parse_codepage(text):
    """Достаёт номер кодовой страницы из вывода `chcp` ("Active code page: 866" и т.п.)."""
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


_console_encoding = None  # кеш: chcp запускаем один раз за работу


def console_encoding():
    """Кодировка вывода системных утилит Windows = активная кодовая страница консоли.

    По умолчанию в русской Windows это CP866, а после `chcp 65001` - UTF-8, поэтому
    жёстко «зашивать» cp866 нельзя. Любая неудача определения -> безопасный cp866.
    """
    global _console_encoding
    if _console_encoding is None:
        _console_encoding = "cp866"
        try:
            raw = subprocess.run(["cmd", "/c", "chcp"], capture_output=True, timeout=5).stdout
            # ASCII-часть вывода содержит номер страницы; русские слова игнорируем
            page = parse_codepage(raw.decode("ascii", errors="ignore"))
            if page == 65001:
                _console_encoding = "utf-8"
            elif page:
                _console_encoding = f"cp{page}"
        except (OSError, subprocess.SubprocessError):
            pass
    return _console_encoding


def pick_encoding(cmd):
    """Системные утилиты Windows - кодировка консоли (обычно cp866), остальное - utf-8."""
    program = os.path.basename(cmd[0]).lower()
    if program.endswith(".exe"):
        program = program[:-4]
    if os.name == "nt" and program in SYSTEM_UTILS:
        return console_encoding()
    return "utf-8"


def make_result(cmd_str, status, returncode, stdout, stderr, elapsed):
    return {
        "command": cmd_str,
        "status": status,
        "returncode": returncode,
        "stdout": stdout or "",
        "stderr": stderr or "",
        "time": elapsed,
    }


def run_command(cmd_str, timeout=TIMEOUT):
    """Запуск одной команды через subprocess.run() с перехватом вывода."""
    cmd = split_command(cmd_str)
    encoding = pick_encoding(cmd)
    start = time.perf_counter()
    if shutil.which(cmd[0]) is None:  # заранее проверяем наличие программы в PATH
        return make_result(
            cmd_str, NOT_FOUND, None, "", f"программа не найдена: {cmd[0]}",
            time.perf_counter() - start,
        )
    try:
        done = subprocess.run(
            cmd,
            capture_output=True,  # stdout=PIPE, stderr=PIPE
            text=True,
            encoding=encoding,
            errors="replace",  # битые байты не роняют скрипт
            timeout=timeout,
            check=True,  # код != 0 -> CalledProcessError
        )
        status, code, out, err = OK, done.returncode, done.stdout, done.stderr
    except FileNotFoundError:
        status, code, out, err = NOT_FOUND, None, "", f"программа не найдена: {cmd[0]}"
    except subprocess.TimeoutExpired:
        # run() сам убивает процесс и вызывает wait() перед тем, как поднять исключение
        status, code, out, err = TIMED_OUT, None, "", f"таймаут {timeout} сек"
    except subprocess.CalledProcessError as exc:
        status, code = ERROR, exc.returncode
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        err = exc.stderr if isinstance(exc.stderr, str) else ""
    except OSError as exc:  # например, PermissionError
        status, code, out, err = ERROR, None, "", f"не удалось запустить: {exc}"
    return make_result(cmd_str, status, code, out, err, time.perf_counter() - start)


def run_parallel(cmds, timeout=TIMEOUT):
    """Параллельный запуск через Popen: сначала стартуем ВСЕ, потом опрашиваем poll().

    Вывод пишем во временные файлы, а не в PIPE: тогда процесс никогда не блокируется
    на переполненном буфере трубы, пока мы опрашиваем другие процессы, и мы можем
    засечь реальное время завершения каждой команды.
    """
    jobs = []  # словари с состоянием каждой команды
    for index, cmd_str in enumerate(cmds):
        cmd = split_command(cmd_str)
        job = {"cmd_str": cmd_str, "cmd": cmd, "result": None, "proc": None,
               "encoding": pick_encoding(cmd), "t0": time.perf_counter()}
        job["out_path"] = f"runner_tmp_{index}_out.txt"
        job["err_path"] = f"runner_tmp_{index}_err.txt"
        try:
            with open(job["out_path"], "wb") as out_f, open(job["err_path"], "wb") as err_f:
                job["proc"] = subprocess.Popen(cmd, stdout=out_f, stderr=err_f)
            job["t0"] = time.perf_counter()
        except FileNotFoundError:
            job["result"] = make_result(cmd_str, NOT_FOUND, None, "",
                                        f"программа не найдена: {cmd[0]}", 0.0)
        except OSError as exc:
            job["result"] = make_result(cmd_str, ERROR, None, "",
                                        f"не удалось запустить: {exc}", 0.0)
        jobs.append(job)

    def read(path, encoding):
        with open(path, "rb") as f:
            return f.read().decode(encoding, errors="replace")

    try:
        while any(job["result"] is None for job in jobs):
            for job in jobs:
                if job["result"] is not None:
                    continue
                proc, elapsed = job["proc"], time.perf_counter() - job["t0"]
                code = proc.poll()  # None - ещё работает
                if code is not None:
                    status = OK if code == 0 else ERROR
                    job["result"] = make_result(
                        job["cmd_str"], status, code,
                        read(job["out_path"], job["encoding"]),
                        read(job["err_path"], job["encoding"]), elapsed)
                elif elapsed > timeout:
                    proc.kill()
                    proc.wait()  # после kill() обязательно ждём завершения
                    job["result"] = make_result(job["cmd_str"], TIMED_OUT, None, "",
                                                f"таймаут {timeout} сек", elapsed)
            time.sleep(0.01)
    finally:
        for job in jobs:  # убираем временные файлы
            for key in ("out_path", "err_path"):
                if os.path.exists(job[key]):
                    os.remove(job[key])
    return [job["result"] for job in jobs]


def _preview(text, full):
    text = text.strip()
    if not text:
        return "(пусто)"
    if not full and len(text) > PREVIEW_LEN:
        text = text[:PREVIEW_LEN] + "…"
    return text.replace("\n", "\n        ")  # выравниваем продолжение строк


def format_report(results, total_time, slow, full=False):
    """Текст отчёта. full=False - превью по 200 символов (консоль), True - целиком (файл)."""
    system = "Windows" if os.name == "nt" else "POSIX"
    lines = [
        f"=== Менеджер запуска команд ({system}) ===",
        f"Режим: {'параллельный (--slow, Popen)' if slow else 'последовательный'}",
        f"Таймаут: {TIMEOUT} сек",
        "Команды: " + "; ".join(r["command"] for r in results),
        "",
    ]
    for number, r in enumerate(results, start=1):
        code = "—" if r["returncode"] is None else r["returncode"]
        lines += [
            f"--- Команда {number}: {r['command']} ---",
            f"Статус: {r['status']}",
            f"Код возврата: {code}",
            f"stdout: {_preview(r['stdout'], full)}",
            f"stderr: {_preview(r['stderr'], full)}",
            f"Время: {r['time']:.2f} сек",
            "",
        ]
    ok = sum(1 for r in results if r["status"] == OK)
    lines += [
        "=== ИТОГО ===",
        f"Всего команд: {len(results)}",
        f"Успешных: {ok}",
        f"Провалившихся: {len(results) - ok}",
        f"Общее время: {total_time:.2f} сек",
    ]
    return "\n".join(lines)


def save_report(text, path=REPORT_FILE):
    with open(path, "w", encoding="utf-8") as f:  # кодировку указываем явно
        f.write(text + "\n")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # русский текст в консоли без кракозябр
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    cmds, slow = parse_args(sys.argv[1:] if argv is None else argv)

    start = time.perf_counter()
    if slow:
        results = run_parallel(cmds)
    else:
        results = [run_command(c) for c in cmds]
    total = time.perf_counter() - start

    print(format_report(results, total, slow))
    save_report(format_report(results, total, slow, full=True))
    print(f"Отчёт сохранён в {REPORT_FILE}")
    sys.exit(0 if any(r["status"] == OK for r in results) else 1)


if __name__ == "__main__":
    main()
```

### Результаты тестирования

> ℹ️ Отчёт готовился в среде Linux, поэтому реальный вывод ниже получен на Linux-аналогах сценариев из задания: `false` вместо `cmd /c exit 1`, `sleep 20` вместо `ping -n 20 127.0.0.1`, `sleep 2` вместо `ping -n 2`, `echo` вместо `cmd /c dir`. Логика программы от ОС не зависит; разница только в ветке кодировки (`os.name == "nt"`). Windows-сценарии указаны в блоке 📌 ниже.

```text
### Запуск 1: обычный режим (успех, нет программы, ненулевой код, русский вывод)
$ python runner.py "python --version" "nonexistent_program_123" "false" "echo привет мир"
=== Менеджер запуска команд (POSIX) ===
Режим: последовательный
Таймаут: 10 сек
Команды: python --version; nonexistent_program_123; false; echo привет мир

--- Команда 1: python --version ---
Статус: успех
Код возврата: 0
stdout: Python 3.12.3
stderr: (пусто)
Время: 0.00 сек

--- Команда 2: nonexistent_program_123 ---
Статус: не найдена
Код возврата: —
stdout: (пусто)
stderr: программа не найдена: nonexistent_program_123
Время: 0.00 сек

--- Команда 3: false ---
Статус: ошибка
Код возврата: 1
stdout: (пусто)
stderr: (пусто)
Время: 0.00 сек

--- Команда 4: echo привет мир ---
Статус: успех
Код возврата: 0
stdout: привет мир
stderr: (пусто)
Время: 0.00 сек

=== ИТОГО ===
Всего команд: 4
Успешных: 2
Провалившихся: 2
Общее время: 0.00 сек
Отчёт сохранён в report.txt
(код возврата: 0)

### Запуск 2: таймаут (sleep 20, лимит 10 сек)
$ python runner.py "sleep 20"
=== Менеджер запуска команд (POSIX) ===
Режим: последовательный
Таймаут: 10 сек
Команды: sleep 20

--- Команда 1: sleep 20 ---
Статус: таймаут
Код возврата: —
stdout: (пусто)
stderr: таймаут 10 сек
Время: 10.01 сек

=== ИТОГО ===
Всего команд: 1
Успешных: 0
Провалившихся: 1
Общее время: 10.01 сек
Отчёт сохранён в report.txt
(код возврата: 1)

### Запуск 3: параллельный режим --slow (2 × sleep 2 + python --version)
$ python runner.py --slow "sleep 2" "sleep 2" "python --version"
=== Менеджер запуска команд (POSIX) ===
Режим: параллельный (--slow, Popen)
Таймаут: 10 сек
Команды: sleep 2; sleep 2; python --version

--- Команда 1: sleep 2 ---
Статус: успех
Код возврата: 0
stdout: (пусто)
stderr: (пусто)
Время: 2.00 сек

--- Команда 2: sleep 2 ---
Статус: успех
Код возврата: 0
stdout: (пусто)
stderr: (пусто)
Время: 2.00 сек

--- Команда 3: python --version ---
Статус: успех
Код возврата: 0
stdout: Python 3.12.3
stderr: (пусто)
Время: 0.01 сек

=== ИТОГО ===
Всего команд: 3
Успешных: 3
Провалившихся: 0
Общее время: 2.02 сек
Отчёт сохранён в report.txt
(код возврата: 0)

### Запуск 3б: те же команды последовательно (для сравнения времени)
$ python runner.py "sleep 2" "sleep 2" "python --version"
Общее время: 4.01 сек

### Запуск 3в: параллельно, с таймаутом и несуществующей программой
$ python runner.py --slow "sleep 15" "no_such_cmd_1" "false"
=== Менеджер запуска команд (POSIX) ===
Режим: параллельный (--slow, Popen)
Таймаут: 10 сек
Команды: sleep 15; no_such_cmd_1; false

--- Команда 1: sleep 15 ---
Статус: таймаут
Код возврата: —
stdout: (пусто)
stderr: таймаут 10 сек
Время: 10.01 сек

--- Команда 2: no_such_cmd_1 ---
Статус: не найдена
Код возврата: —
stdout: (пусто)
stderr: программа не найдена: no_such_cmd_1
Время: 0.00 сек

--- Команда 3: false ---
Статус: ошибка
Код возврата: 1
stdout: (пусто)
stderr: (пусто)
Время: 0.01 сек

=== ИТОГО ===
Всего команд: 3
Успешных: 0
Провалившихся: 3
Общее время: 10.02 сек
Отчёт сохранён в report.txt
(код возврата: 1)
report.txt
runner.py

### Запуск 4: без аргументов
$ python runner.py
(код возврата: 0)
Предупреждение: команды не переданы, используется `python --version`
=== Менеджер запуска команд (POSIX) ===
Режим: последовательный
Таймаут: 10 сек
Команды: python --version

--- Команда 1: python --version ---
Статус: успех
Код возврата: 0
stdout: Python 3.12.3
stderr: (пусто)
Время: 0.00 сек

=== ИТОГО ===
Всего команд: 1
Успешных: 1
Провалившихся: 0
Общее время: 0.00 сек
Отчёт сохранён в report.txt

### Запуск 5: все команды провалились -> код 1
$ python runner.py "false" "no_such_cmd_1"
(код возврата: 1)
=== ИТОГО ===
Всего команд: 2
Успешных: 0
Провалившихся: 2
Общее время: 0.00 сек
Отчёт сохранён в report.txt

### Содержимое report.txt после запуска 5
=== Менеджер запуска команд (POSIX) ===
Режим: последовательный
Таймаут: 10 сек
Команды: false; no_such_cmd_1

--- Команда 1: false ---
Статус: ошибка
Код возврата: 1
stdout: (пусто)
stderr: (пусто)
Время: 0.00 сек

--- Команда 2: no_such_cmd_1 ---
Статус: не найдена
Код возврата: —
stdout: (пусто)
stderr: программа не найдена: no_such_cmd_1
Время: 0.00 сек

=== ИТОГО ===
Всего команд: 2
Успешных: 0
Провалившихся: 2
Общее время: 0.00 сек
```

**Что подтверждают запуски.** Успех/ошибка/таймаут/«не найдена» различаются статусом и кодом возврата; программа не останавливается на проблемной команде; таймаут срабатывает через 10 с; в режиме `--slow` три команды ушли параллельно, общее время ≈ 2 с (последовательно те же команды — 4 с), а время каждой команды измеряется отдельно (`python --version` — 0.01 с, а не 2 с); без аргументов запускается `python --version` с предупреждением; если все команды провалены — код возврата 1; временные файлы параллельного режима удаляются; `report.txt` содержит полный отчёт в UTF-8.

**Вспомогательные эксперименты (реальный вывод)** — безопасность, кодировки, `which`, взаимная блокировка труб, `kill()` без `wait()`, `check=True`:

```text
### 1. split_command: опасная строка разбирается в СПИСОК, шелл не участвует
['cmd', '/c', 'del', '/q', '*']

### 2. Инъекция: os.system (через shell) vs subprocess.run со списком (аналог & из Windows)
os.system   -> ВЫПОЛНИЛАСЬ_ВТОРАЯ_КОМАНДА
file.txt
subprocess.run([...]) -> file.txt & echo ВЫПОЛНИЛАСЬ_ВТОРАЯ_КОМАНДА

### 3. Кодировки: байты cp866 прочитаны правильно и неправильно
байты        : b'\x8e\xa1\xac\xa5\xad \xaf\xa0\xaa\xa5\xe2\xa0' ...
cp866  (верно): Обмен пакетами с 8.8.8.8
cp1251 (ошибка): ЋЎ¬Ґ­ Ї ЄҐв ¬Ё б 8.8.8.8
utf-8  (ошибка): ����� ����⠬� � 8.8.8.8
pick_encoding на этой ОС (os.name='posix'): dir->utf-8, python->utf-8

### 4. shutil.which
which('python') = /usr/bin/python
which('sleep') = /usr/bin/sleep
which('findstr') = None
which('nonexistent_program_123') = None
run(['nonexistent_program_123']) -> FileNotFoundError [Errno 2] No such file or directory: 'nonexistent_program_123'

### 5. Взаимная блокировка при чтении труб по очереди
wait(timeout=2): TimeoutExpired - дочерний процесс завис на записи в stderr (буфер трубы полон)
communicate(): stdout='конец', длина stderr=300000, код=0

### 6. kill() без wait() -> процесс-зомби
после kill(), до wait(): Z (zombie)
после wait(): returncode = -9 | /proc/493 существует: False

### 7. check=True и CalledProcessError
CalledProcessError: returncode = 1 | cmd = ['false']
```

> 📌 **Выполните на Windows и вставьте вывод** (эти сценарии из раздела 5 задания на Linux не воспроизводятся):
> ```
> chcp 65001
> python runner.py "python --version" "ping -n 2 8.8.8.8" "nonexistent_program_123"
> python runner.py "ping -n 20 127.0.0.1"              (таймаут 10 с)
> python runner.py --slow "ping -n 2 8.8.8.8" "ping -n 2 1.1.1.1" "python --version"
> python runner.py "cmd /c dir"                        (русские буквы читаются корректно)
> python runner.py "cmd /c exit 1"                     (статус «ошибка», код 1)
> ```

## Раздел 3. Таблица промптов и ответов ИИ

| № | Промпт (запрос к ИИ) | Ответ ИИ (кратко) | Анализ результата |
| --- | --- | --- | --- |
| 1 | «Почему `os.system` считается небезопасным? Покажи пример инъекции команд для Windows с `&` и объясни, почему со списком аргументов в `subprocess.run` она невозможна.» | `os.system` отдаёт строку интерпретатору `cmd.exe`, метасимволы `&`, `\|`, `>` выполняются как команды. В `subprocess.run([...])` без `shell=True` аргументы передаются программе как есть, без разбора шеллом. | Проверил на практике (Linux, где `&` тоже метасимвол): `os.system("echo file.txt & echo ВТОРАЯ")` выполнила обе команды, а `subprocess.run(["echo", "file.txt", "&", "echo", "ВТОРАЯ"])` напечатала строку целиком (вывод в разделе «Вспомогательные эксперименты»). |
| 2 | «В чём разница между `subprocess.run` и `subprocess.Popen`? Как запустить три программы одновременно и узнать время каждой?» | `run` ждёт завершения и возвращает `CompletedProcess`; `Popen` сразу возвращает объект процесса, им управляют через `poll`, `wait`, `communicate`, `kill`. Для параллельности — запустить все `Popen`, затем опрашивать. | Сначала собирал результаты `communicate()` по очереди — время всех команд получалось одинаковым (ждал самую долгую), см. улучшение №1. Перешёл на опрос `poll()`. |
| 3 | «Почему `subprocess.run(["dir"])` падает с `FileNotFoundError`, а `findstr` работает? Как запустить `dir`?» | `dir` — встроенная команда `cmd.exe`, отдельного `.exe` нет; нужно `["cmd", "/c", "dir"]`. `findstr.exe`, `ping.exe`, `where.exe` — обычные программы. | Согласуется с теорией задания. Реализовал в `pick_encoding` список системных утилит, включающий `cmd`. Проверить на Windows (блок 📌). |
| 4 | «Как правильно перехватить stdout и stderr одновременно? Почему нельзя читать `p.stdout` и `p.stderr` по очереди?» | `capture_output=True` или `stdout=PIPE, stderr=PIPE` + `communicate()`. Буфер трубы ограничен (около 64 КБ): если дочерний процесс заполнил stderr, а родитель ждёт stdout, возникает взаимная блокировка. `communicate()` читает оба потока одновременно. | Воспроизвёл блокировку: процесс, пишущий 300 000 символов в stderr, не завершился за `wait(timeout=2)`, а `communicate()` отработал (вывод в «Вспомогательных экспериментах»). |
| 5 | «Почему вывод системных утилит Windows читается как CP866, а вывод Python-скриптов — как UTF-8? Как выбрать кодировку автоматически?» | Консольные утилиты пишут в OEM-кодировке консоли (CP866 в русской Windows), Python со своей настройкой — в UTF-8. Выбирать по имени программы или по активной кодовой странице (`chcp`). | Реализовал `pick_encoding`; ИИ не предупредил, что после `chcp 65001` системные утилиты тоже пишут UTF-8 — поэтому добавил `console_encoding()`: читаю номер страницы из вывода `chcp` и при ошибке откатываюсь на `cp866` (улучшение №4). Показал на реальных байтах, как выглядят неверные кодировки. |
| 6 | «Что делает `shutil.which`? Как с его помощью избежать `FileNotFoundError`? Что будет, если после `kill()` не вызвать `wait()`?» | `which` ищет программу в `PATH` (в Windows учитывает `PATHEXT`) и возвращает путь или `None`. Без `wait()` после `kill()` процесс остаётся зомби (POSIX) или с неосвобождённым дескриптором (Windows). | Добавил проверку `shutil.which` перед запуском, исключение оставил на случай гонки. Зомби проверил в Linux через `/proc/<pid>/status` (состояние `Z`) до и после `wait()`. |
| 7 | «Вот мой `runner.py` (вставляю код). Найди 2 потенциальные проблемы: что может пойти не так на разных ОС?» | (1) Время в параллельном режиме считается неверно, если ждать процессы по очереди. (2) При таймауте `cmd /c ping ...` в Windows `kill()` убивает только `cmd.exe`, а `ping.exe` остаётся. | Первое подтвердилось (улучшение №1). Второе — особенность Windows: в `run()` таймаут завершает только непосредственный процесс; для деревьев процессов нужен `taskkill /T` (в работе не требуется, отмечаю как ограничение). |

## Раздел 4. Таблица улучшений кода

Улучшения №1 и №4 — реальные изменения между версиями `runner.py`; в №2, №3 и №5 «старый код» — черновые решения, а проблема первого из них воспроизведена запуском (раздел «Вспомогательные эксперименты»).

| № | Старый код (фрагмент) | Новый код (фрагмент) | Пояснение (зачем изменено) |
| --- | --- | --- | --- |
| 1 | `proc = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)`<br>... затем по очереди:<br>`out_b, err_b = proc.communicate(timeout=remaining)`<br>`elapsed = time.perf_counter() - t0` | `proc = subprocess.Popen(cmd, stdout=out_f, stderr=err_f)` (временные файлы)<br>`while any(job["result"] is None for job in jobs):`<br>`    code = proc.poll()`<br>`    ...`<br>`    time.sleep(0.01)` | В первой версии у `python --version` в режиме `--slow` печаталось «Время: 2.00 сек» — оно ждало более долгие команды. Опрос `poll()` фиксирует настоящий момент завершения (теперь 0.01 с). Вывод в файлы исключает блокировку при переполнении буфера трубы. |
| 2 | `os.system(f"echo {user_input}")` (опасный вариант, продемонстрирован в тестах) | `cmd = cmd_str.split()`<br>`subprocess.run(cmd, capture_output=True, text=True, ...)` без `shell=True` | `"file.txt & del /q *"` становится обычным списком аргументов, ни `&`, ни `\|` не интерпретируются; плюс появляется перехват вывода, таймаут и код возврата. |
| 3 | `subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)` | `subprocess.run(cmd, ..., errors="replace", timeout=timeout, check=True)`<br>`except subprocess.CalledProcessError as exc: status, code = ERROR, exc.returncode` | `check=True` превращает ненулевой код в `CalledProcessError`, который обрабатывается отдельно от таймаута и «не найдена»; `errors="replace"` не даёт упасть на «битых» байтах другой кодировки. |
| 4 | `if program in SYSTEM_UTILS:`<br>`    return "cp866"` | `if os.name == "nt" and program in SYSTEM_UTILS:`<br>`    return console_encoding()`<br>(`console_encoding()` читает номер страницы из `chcp`, `65001` → `utf-8`, ошибка → `cp866`) | Жёстко заданный `cp866` ломается после рекомендованного заданием `chcp 65001`, когда системные утилиты уже пишут UTF-8. Определение по активной кодовой странице работает в обоих случаях, а откат на `cp866` сохраняет поведение из задания. Разбор номера страницы (`parse_codepage`) проверен на строках «Active code page: 866/65001/1251». |
| 5 | (в `run_command` сразу `subprocess.run(...)`) | `if shutil.which(cmd[0]) is None:`<br>`    return make_result(cmd_str, NOT_FOUND, None, "", f"программа не найдена: {cmd[0]}", ...)` | Предварительная проверка в `PATH` даёт понятное сообщение без попытки запуска; `except FileNotFoundError` остаётся на случай гонки (программу удалили между проверкой и запуском). |

## Раздел 5. Ответы на контрольные вопросы

**1. Почему `os.system` устарел и небезопасен? Пример инъекции для Windows.**
`os.system(command)` передаёт строку командному интерпретатору, поэтому метасимволы в пользовательском вводе выполняются как команды: `filename = "file.txt & del /q *"; os.system(f"type {filename}")` выполнит `type file.txt` **и** `del /q *` (аналогично с `|` и `&&`). Кроме того, он не перехватывает вывод, не даёт таймаута и управления процессом, зависит от платформы и официально заменён модулем `subprocess`.

**2. Разница между `subprocess.run()` и `subprocess.Popen()`. Когда что предпочтительнее?**
`run()` — высокоуровневая обёртка: запускает процесс, ждёт завершения, возвращает `CompletedProcess` (`returncode`, `stdout`, `stderr`), умеет `timeout` и `check`. `Popen` — низкоуровневый интерфейс: возвращает объект сразу, процесс работает в фоне; даёт `poll`, `wait`, `communicate`, `kill`, потоковое чтение вывода и запись в stdin. `run` — для обычных «запустил и получил результат», `Popen` — для параллельного запуска, интерактивного обмена и потоковой обработки.

**3. Почему `subprocess.run(["ls", "-l"])` падает с `FileNotFoundError` в Windows? Как выполнить аналог?**
В Windows нет программы `ls.exe`, а `subprocess` ищет исполняемый файл в `PATH`. Аналог — команда `dir`: `["cmd", "/c", "dir"]`.

**4. Почему `subprocess.run(["dir"])` тоже не работает?**
`dir` — встроенная команда интерпретатора `cmd.exe`, отдельного исполняемого файла нет. Нужно запускать сам `cmd` с ключом `/c`: `["cmd", "/c", "dir"]` (то же для `type`, `echo`, `cd`, `exit`). Автономные `.exe` (`findstr`, `ping`, `where`) запускаются напрямую.

**5. Как перехватить stdout и stderr одновременно? Почему нельзя читать их по очереди без `communicate()`?**
`capture_output=True` (или `stdout=PIPE, stderr=PIPE`); можно слить потоки через `stderr=subprocess.STDOUT`. Читать по очереди нельзя: буфер трубы конечен, и если процесс заполнил stderr, пока родитель читает stdout (или наоборот), оба ждут друг друга — взаимная блокировка. `communicate()` читает оба потока одновременно и ждёт завершения (проверено: `wait(timeout=2)` на процессе, пишущем 300 000 символов в stderr, истекает, а `communicate()` завершается).

**6. Что произойдёт при `timeout=N`, если процесс не успел завершиться? Как поймать?**
Будет поднято `subprocess.TimeoutExpired`; `run()` перед этим сам убивает процесс и ждёт его завершения. Ловится `except subprocess.TimeoutExpired:`. При использовании `Popen.communicate(timeout=...)` процесс сам не убивается — нужно вызвать `kill()` и затем `communicate()`/`wait()`. В Windows `kill()` завершает только непосредственный процесс, но не его потомков.

**7. Зачем `check=True`? Какое исключение и когда?**
С `check=True` при ненулевом коде возврата поднимается `subprocess.CalledProcessError` (атрибуты `returncode`, `cmd`, `stdout`, `stderr`). Это превращает «тихую» ошибку в исключение, которое нельзя случайно проигнорировать; в `runner.py` оно определяет статус «ошибка».

**8. Почему системные утилиты Windows читаются как CP866, а Python-скрипты как UTF-8? Как исправить?**
Консольные программы (`cmd`, `dir`, `findstr`, `ping`) пишут байты в OEM-кодировке консоли — в русской Windows CP866; Python-скрипт с `reconfigure(encoding="utf-8")` пишет UTF-8. Если декодировать неверно, получаются «кракозябры» (в тестах: байты «Обмен пакетами» как CP1251 превращаются в «ЋЎ¬Ґ­ Ї ЄҐв ¬Ё»). Исправление: `encoding="cp866"` для системных утилит и `utf-8` для Python (`pick_encoding`), либо определять реальную страницу через `chcp`, либо переключить консоль на UTF-8 (`chcp 65001`).

**9. Что делает `shutil.which("program")`? Как предотвратить `FileNotFoundError`?**
Ищет программу в `PATH` (в Windows — с учётом `PATHEXT`) и возвращает полный путь или `None`. Перед запуском проверяем `if shutil.which(name) is None:` и выдаём «программа не найдена», не пытаясь запускать. Проверка не исключает гонки, поэтому `except FileNotFoundError` всё равно нужен.

**10. Что будет, если после `p.kill()` не вызвать `p.wait()`?**
Процесс завершён, но его код возврата никто не забрал: в Linux он остаётся «зомби» (`State: Z` — проверено через `/proc`), в Windows остаётся неосвобождённым дескриптор; `returncode` не заполнен. После `wait()` ресурсы освобождаются (в тесте `returncode = -9`).

**11. В чём опасность `shell=True`? Когда он нужен и как обезопасить данные?**
Команда передаётся шеллу, и метасимволы в данных превращаются в чужие команды (инъекция). Он нужен для возможностей самого шелла: встроенные команды `cmd`, конвейеры `\|`, перенаправления, подстановка шаблонов. Безопаснее обходиться списком аргументов (`["cmd", "/c", "dir"]`); если `shell=True` неизбежен, нельзя подставлять непроверенный ввод: валидировать по белому списку, экранировать (`shlex.quote` в POSIX, `subprocess.list2cmdline` в Windows) и не строить строку конкатенацией.

**12. Как переключить консоль Windows в UTF-8? Зачем?**
Командой `chcp 65001` (текущая страница проверяется просто `chcp`). Тогда русский текст в консоли отображается корректно, а для вывода можно использовать единую кодировку UTF-8 — меньше путаницы между CP866/CP1251/UTF-8. Учитывая, что после этого и системные утилиты пишут UTF-8, в `runner.py` кодировка определяется по активной странице консоли.

## Раздел 6. Выводы

В работе я научился управлять внешними программами из Python через `subprocess`: запускать их со списком аргументов без шелла, перехватывать вывод, ограничивать время выполнения и обрабатывать три класса сбоев (программа не найдена, таймаут, ненулевой код). Я увидел на практике, почему `os.system` опасен, и проверил, что в `subprocess.run` со списком метасимволы не выполняются. Самым сложным оказался параллельный режим: ожидание процессов по очереди давало неверное время, а чтение труб без `communicate()` приводит к взаимной блокировке; решением стали опрос `poll()` и вывод во временные файлы. Разобрался с особенностями Windows (встроенные команды `cmd`, кодировка CP866 против UTF-8) и сделал определение кодировки устойчивым к `chcp 65001`. Самый полезный навык — всегда продумывать три ситуации: программы нет, программа зависла и программа вернула ошибку. Windows-сценарии из задания необходимо выполнить на целевой ОС (см. блок 📌), логика программы на Linux-аналогах проверена. Я понимаю код `runner.py` и могу объяснить его функции.
