**Менеджер процессов**

```bash
python lab6_runner/runner.py
```
```bash
python lab6_runner/runner.py "python --version" "ping -n 2 8.8.8.8" "cmd /c exit 1" "nonexistent_program_123" "cmd /c dir" "ping -n 20 127.0.0.1"
```

```bash
python lab6_runner/runner.py --slow "ping -n 2 8.8.8.8" "ping -n 2 1.1.1.1" "python --version"
```