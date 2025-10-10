import re
from pathlib import Path
p = Path('website/templates/website/home.html')
text = p.read_text(encoding='utf-8')
# Find template tags of interest
pattern = re.compile(r"({%\s*(if|endif|for|endfor|empty|elif|else)[^%]*%})")
stack = []
line_offsets = [0]
for i, ch in enumerate(text):
    if ch == '\n':
        line_offsets.append(i+1)

errors = []
for m in pattern.finditer(text):
    tag_full = m.group(1)
    inner = m.group(2)
    # determine line number
    pos = m.start(1)
    # binary search for line
    import bisect
    line = bisect.bisect_right(line_offsets, pos)
    print(f"Line {line}: {tag_full}")
    if inner == 'if':
        stack.append(('if', line))
    elif inner == 'for':
        stack.append(('for', line))
    elif inner == 'empty':
        # empty must be inside a for
        if not stack or stack[-1][0] != 'for':
            errors.append((line, 'empty outside for'))
    elif inner == 'endif':
        if not stack:
            errors.append((line, 'endif with empty stack'))
        else:
            # pop until matching if
            if stack[-1][0] == 'if':
                stack.pop()
            else:
                errors.append((line, f"endif found but top is {stack[-1][0]} started at line {stack[-1][1]}"))
    elif inner == 'endfor':
        if not stack:
            errors.append((line, 'endfor with empty stack'))
        else:
            if stack[-1][0] == 'for':
                stack.pop()
            else:
                errors.append((line, f"endfor found but top is {stack[-1][0]} started at line {stack[-1][1]}"))

print('\nStack after pass:')
for item in stack:
    print(item)

if errors:
    print('\nErrors:')
    for e in errors:
        print(e)
    raise SystemExit(1)
else:
    print('\nNo errors found')
