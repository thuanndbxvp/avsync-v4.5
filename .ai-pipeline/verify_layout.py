import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\Admin\AppData\Local\Temp\index.html', 'r', encoding='utf-8') as f:
    html = f.read()
print('topic-meta found:', 'id="topic-meta"' in html)
print('finance-topic-detail found:', 'id="finance-topic-detail"' in html)
print('finance-niche-panel collapsed:', 'id="finance-niche-panel" class="workshop-config-panel collapsed"' in html)
print('finance-niche-panel open:', 'id="finance-niche-panel" class="workshop-config-panel"' in html)
print('Chú que tài chính occurrences:', html.count('Chú que tài chính'))
print('Old brand "Chú Quế Tài Chính" present:', 'Chú Quế Tài Chính' in html)
print('Header height var:', '--header-height: 36px' in html)
print('Footer height var:', '--footer-height: 28px' in html)
