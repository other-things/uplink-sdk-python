import codecs


def hexkey(key):
    return codecs.encode(key.to_string(), 'hex')


def to_bytes(n, length, byteorder='big'):
    # int.to_bytes for both python 2 and 3
    # copied from https://stackoverflow.com/a/20793663 and made python 3 compatible
    h = '%x' % n
    s = codecs.decode(('0' * (len(h) % 2) + h).zfill(length * 2), 'hex')
    return s if byteorder == 'big' else s[::-1]
