from pathlib import Path
ROOT = Path("D:/AIWriteX")
for sub in ["docs/dna", "scripts", "src/ai_write_x/niches", "src/ai_write_x/web/api", "src/ai_write_x/web/locales", "src/content"]:
    p = ROOT / sub
    if p.exists():
        files = list(p.rglob("*"))
        files = [f for f in files if f.is_file()]
        print(f"{sub}: {len(files)} files")
        for f in files[:15]:
            print(f"  {f.relative_to(ROOT)} ({f.stat().st_size} bytes)")
        if len(files) > 15:
            print(f"  ... +{len(files)-15} more")
        print()