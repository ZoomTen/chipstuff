import os, sys, pprint
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from ftmlib import FamitrackerModule

fami = FamitrackerModule()
fami.load_from_file(sys.argv[1])

print("\nFamitracker module object")
print(fami)

print("\nFamitracker module contents")
pprint.pprint(fami.module)

print("\nFamitracker module patterns")
for i in fami.get_songs():
	print(f"--- {i['name']} ---")
	for pattern in i['patterns']:
		print(f'\n{pattern}')
		for row in pattern.content:
			print(row)
