import sys
sys.path.insert(0, '.')
from extractors.schindler import extract_from_pdf, get_param_descriptions

result = extract_from_pdf('/mnt/user-data/uploads/planos_lift.pdf')
desc = get_param_descriptions()

print('=== FOUND ===')
for k, v in sorted(result['found'].items()):
    print(f'  {k:8} = {v:>10}   ({desc.get(k, "")})')

print()
print('=== MISSING ===')
for k in sorted(result['missing']):
    print(f'  {k:8}   ({desc.get(k, "")})')
