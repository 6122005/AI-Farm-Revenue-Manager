import re
with open("output_matrix.md", "r") as f:
    text = f.read()

# The markdown table starts with '| Slot'
lines = text.split('\n')
table_lines = []
in_table = False
for line in lines:
    if line.startswith('| Slot'):
        in_table = True
    if in_table:
        if not line.strip() and len(table_lines) > 0:
            break
        table_lines.append(line)

with open("final_table.md", "w") as f:
    f.write("\n".join(table_lines))
