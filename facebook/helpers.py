from time import time
import xxhash


def xxhasher(seed):
    def xhash(inc):
        x = xxhash.xxh64(seed=seed)
        x.update(inc)
        return x.hexdigest()

    return xhash


def msec():
    return round(time()*1000)
