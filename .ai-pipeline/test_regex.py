import re
topic = "7 thói quen tài chính của người 30 tuổi"
pat = r"(\d+)\s*(nghề|cách|điều|thứ|thói quen|nguyên tắc|tài sản|khoản)"
print("pattern:", repr(pat))
print("topic:  ", repr(topic))
m = re.search(pat, topic)
print("match:", m)
if m:
    print("matched group:", m.group())