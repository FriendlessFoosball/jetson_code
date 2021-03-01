import csv
import pickle

FILE = 'offense.calib'

calib = pickle.load(open(FILE, 'rb'))

x = list(calib.keys())
l = []
r = []

for val in calib.values():
    ls, rs = zip(*val)
    l.append(sum(ls) / len(ls))
    r.append(sum(rs) / len(rs))

x = [i if i <= 180 else i - 360 for i in x]

to_e = [tuple(i) for i in zip(x, l, r)]
to_e.sort()

print(to_e)

with open('offense.anglecal', 'wb') as f:
    pickle.dump(to_e, f)