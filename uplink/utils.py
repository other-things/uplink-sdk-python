import codecs


def hexkey(key):
    return codecs.encode(key.to_string(), 'hex')
