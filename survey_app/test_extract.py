from extractors.schindler import extract_from_pdf
result = extract_from_pdf('/mnt/user-data/uploads/planos_lift.pdf')
for k, v in sorted(result.items()):
    print('OK  ' if v is not None else 'MISS', k, '=', v)
