"""Probe after fix: no Accept-Language header should now return Vietnamese."""
import urllib.request

print("=== no Accept-Language header (was zh, should now be vi) ===")
req = urllib.request.Request("http://127.0.0.1:8000/")
r = urllib.request.urlopen(req, timeout=5)
body = r.read().decode("utf-8")
title = body[body.find("<title>"):body.find("</title>") + 8]
print(f"  title: {title!r}")

# Strip BOM/encoding issues by counting actual chars
import re
cjk = sum(1 for c in body if "一" <= c <= "鿿")
vi = sum(1 for c in body if "à" <= c <= "ỹ")
print(f"  cjk chars: {cjk}, vi chars: {vi}")

print()
print("=== with Accept-Language: zh-CN (should still be zh, untouched) ===")
req = urllib.request.Request("http://127.0.0.1:8000/")
req.add_header("Accept-Language", "zh-CN")
r = urllib.request.urlopen(req, timeout=5)
body = r.read().decode("utf-8")
title = body[body.find("<title>"):body.find("</title>") + 8]
print(f"  title: {title!r}")
cjk = sum(1 for c in body if "一" <= c <= "鿿")
vi = sum(1 for c in body if "à" <= c <= "ỹ")
print(f"  cjk chars: {cjk}, vi chars: {vi}")

print()
print("=== with Accept-Language: en (should be vi, English Vietnamese) ===")
req = urllib.request.Request("http://127.0.0.1:8000/")
req.add_header("Accept-Language", "en")
r = urllib.request.urlopen(req, timeout=5)
body = r.read().decode("utf-8")
title = body[body.find("<title>"):body.find("</title>") + 8]
print(f"  title: {title!r}")