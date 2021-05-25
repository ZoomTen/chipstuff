import os, sys, pprint
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from deflelib import DeflemaskModule

dmf = DeflemaskModule()
dmf.load_from_file(sys.argv[1])

print("\nDeflemask module object")
print(dmf)

print("\nDeflemask module contents")
pprint.pprint(dmf.module)
