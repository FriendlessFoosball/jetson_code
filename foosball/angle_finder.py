import pickle
import itertools

GOALIE_MAX = 104.4
GOALIE_MIN = -82.8

OFFENSE_MAX = 79.2
OFFENSE_MIN = -97.2

MEMO = {}

with open('calibrations/goalie.anglecal', 'rb') as f:
    GOALIE_CAL = [i for i in pickle.load(f) if GOALIE_MIN <= i[0] and GOALIE_MAX >= i[0]]

with open('calibrations/offense.anglecal', 'rb') as f:
    OFFENSE_CAL = [i for i in pickle.load(f) if OFFENSE_MIN <= i[0] and OFFENSE_MAX >= i[0]]


def find_solutions(target, idx, data):
    sols = []

    for a, b in zip(data, data[1:]):
        lo = min(a[idx], b[idx])
        hi = max(a[idx], b[idx])

        if lo <= target and target <= hi:
            if target == lo and target == hi:
                if a[0] < 0:
                    if len(sols) == 0:
                        sols.append((a[0] + b[0]) / 2)
                else:
                    sols = [(a[0] + b[0]) / 2]
            else:
                if a[idx] < b[idx]:
                    lloc = a[0]
                    hloc = b[0]
                else:
                    lloc = b[0]
                    hloc = a[0]

                p = (target - lo) / (hi - lo)
                sols.append(lloc + p * (hloc - lloc))

    return sols


def dist(a1, a2):
    a = min(a1, a2)
    b = max(a1, a2)

    return min(b - a, a - b + 360)


def avgangle(a1, a2):
    a = min(a1, a2)
    b = max(a1, a2)

    if b - a < a - b + 360:
        return (a + b) / 2
    else:
        tmp = (a + b + 360) / 2
        if tmp > 180:
            tmp -= 360

        return tmp

def find_angle(l, r, isGoalie):
    if (l, r, isGoalie) in MEMO:
        return MEMO[(l, r, isGoalie)]
    else:
        data = GOALIE_CAL if isGoalie else OFFENSE_CAL

        l_sols = find_solutions(l, 1, data)
        r_sols = find_solutions(r, 2, data)

        if len(l_sols) == 0:
            if l < 25:
                if isGoalie:
                    l_sols.append(-72)
                else:
                    l_sols.append(-93.6)
            else:
                if isGoalie:
                    l_sols.append(10.8)
                else:
                    l_sols.append(-7.2)
        
        if len(r_sols) == 0:
            if r < 90:
                if isGoalie:
                    r_sols.append(10.8)
                else:
                    r_sols.append(-10.8)
            else:
                if isGoalie:
                    r_sols.append(108)
                else:
                    r_sols.append(90)

        min_diff = 360
        angle = None

        for la, ra in itertools.product(l_sols, r_sols):
            if dist(la, ra) < min_diff:
                angle = avgangle(la, ra)
                min_diff = dist(la, ra)

        if min_diff > 30:
            return r_sols[0]

        MEMO[(l, r, isGoalie)] = angle

        return angle