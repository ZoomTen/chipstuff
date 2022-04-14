import furnacelib

if __name__ == "__main__":
    import sys
    import pprint
    pp = pprint.PrettyPrinter(4)

    module = furnacelib.FurnaceModule(file_name=sys.argv[1])
    p = [i["index"] for i in module.patterns]
    p = list(set(p))
    print(p)
    for i in module.order:
    	print("%02d\t%s" % (i, module.order[i]))
