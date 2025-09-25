from pathlib import Path
import re, argparse

def cat(path):
    print(Path(path).read_text(encoding='utf-8', errors='ignore'))

def grep(path, pattern):
    rx = re.compile(pattern)
    for i, line in enumerate(Path(path).read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
        if rx.search(line):
            print(f"{i:04d}: {line}")

def replace(path, pattern, repl):
    p = Path(path)
    text = p.read_text(encoding='utf-8', errors='ignore')
    new = re.sub(pattern, repl, text, flags=re.S)
    if new != text:
        p.write_text(new, encoding='utf-8')
    print('OK')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c1 = sub.add_parser('cat');     c1.add_argument('path')
    c2 = sub.add_parser('grep');    c2.add_argument('path'); c2.add_argument('pattern')
    c3 = sub.add_parser('replace'); c3.add_argument('path'); c3.add_argument('pattern'); c3.add_argument('repl')
    args = ap.parse_args()
    globals()[args.cmd](**{k:v for k,v in vars(args).items() if k!='cmd'})
