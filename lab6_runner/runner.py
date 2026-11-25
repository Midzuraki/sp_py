import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

TIMEOUT = 10
BASE_DIR = Path(__file__).resolve().parent
REPORT_FILE = BASE_DIR / "report.txt"
PREVIEW_LEN = 200
SYSTEM_UTILS = {"cmd", "findstr", "ping", "where", "dir", "type", "timeout"}

OK, ERROR, TIMED_OUT, NOT_FOUND = "успех", "ошибка", "таймаут", "не найдена"


def parse_args(argv):
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
    if os.name == "nt":
        return [arg.strip("\"'") for arg in shlex.split(cmd_str, posix=False)]
    return shlex.split(cmd_str)


def parse_codepage(text):
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


_console_encoding = None


def console_encoding():
    global _console_encoding
    if _console_encoding is None:
        _console_encoding = "cp866"
        try:
            raw = subprocess.run(["cmd", "/c", "chcp"], capture_output=True, timeout=5).stdout
            page = parse_codepage(raw.decode("ascii", errors="ignore"))
            if page == 65001:
                _console_encoding = "utf-8"
            elif page:
                _console_encoding = f"cp{page}"
        except (OSError, subprocess.SubprocessError):
            pass
    return _console_encoding


def pick_encoding(cmd):
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
    cmd = split_command(cmd_str)
    encoding = pick_encoding(cmd)
    start = time.perf_counter()
    if shutil.which(cmd[0]) is None:
        return make_result(
            cmd_str, NOT_FOUND, None, "", f"программа не найдена: {cmd[0]}",
            time.perf_counter() - start,
        )
    try:
        done = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            timeout=timeout,
            check=True,
        )
        status, code, out, err = OK, done.returncode, done.stdout, done.stderr
    except FileNotFoundError:
        status, code, out, err = NOT_FOUND, None, "", f"программа не найдена: {cmd[0]}"
    except subprocess.TimeoutExpired:
        status, code, out, err = TIMED_OUT, None, "", f"таймаут {timeout} сек"
    except subprocess.CalledProcessError as exc:
        status, code = ERROR, exc.returncode
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        err = exc.stderr if isinstance(exc.stderr, str) else ""
    except OSError as exc:
        status, code, out, err = ERROR, None, "", f"не удалось запустить: {exc}"
    return make_result(cmd_str, status, code, out, err, time.perf_counter() - start)


def run_parallel(cmds, timeout=TIMEOUT):
    jobs = []
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
                code = proc.poll()
                if code is not None:
                    status = OK if code == 0 else ERROR
                    job["result"] = make_result(
                        job["cmd_str"], status, code,
                        read(job["out_path"], job["encoding"]),
                        read(job["err_path"], job["encoding"]), elapsed)
                elif elapsed > timeout:
                    proc.kill()
                    proc.wait()
                    job["result"] = make_result(job["cmd_str"], TIMED_OUT, None, "",
                                                f"таймаут {timeout} сек", elapsed)
            time.sleep(0.01)
    finally:
        for job in jobs:
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
    return text.replace("\n", "\n        ")


def format_report(results, total_time, slow, full=False):
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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
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
