import codecs
s = r"(\d+)\s*(nghề|cách)"
print("original:", repr(s))
try:
    decoded = codecs.decode(s, "unicode_escape")
    print("decoded:", repr(decoded))
except Exception as e:
    print("error:", e)
print()
# What's actually in the YAML file?
s2 = "(\\d+)\\s*(nghề|cách)"
print("file value:", repr(s2))
try:
    decoded2 = codecs.decode(s2, "unicode_escape")
    print("file decoded:", repr(decoded2))
except Exception as e:
    print("file error:", e)