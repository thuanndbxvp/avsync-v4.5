"""Find remaining CJK phrases in served HTML that aren't translated."""
import urllib.request, re

with urllib.request.urlopen('http://localhost:8000/') as r:
    body = r.read().decode('utf-8')

# Find all CJK runs
runs = re.findall(r'[一-鿿]+', body)
from collections import Counter
ctr = Counter(runs)

# Filter out very short ones and show top
print('Top remaining CJK phrases:')
for phrase, count in ctr.most_common(80):
    if len(phrase) >= 2:
        print(f'  {count:4}x  {phrase}')