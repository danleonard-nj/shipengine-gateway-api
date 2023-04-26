
def first_or_default(_iterable):
    try:
        return _iterable[0]
    except:
        return None


def apply(obj, func):
    return func(obj)


def hours_to_seconds(hours):
    return hours * 60 * 60
