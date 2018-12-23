import itertools, logging, copy


def print_entry_exit(func):
    def wrapper(*args, **kwargs):
        print('Entering', func)
        result = func(*args, **kwargs)
        print('Exiting', func)
        return result

    return wrapper


def log_entry_exit(logger=None, level=logging.DEBUG):
    if logger is None:
        logger = logging.getLogger()

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.log(level, 'Entering %s', str(func))
            result = func(*args, **kwargs)
            logger.log(level, 'Exiting %s', str(func))
            return result

        return wrapper

    return decorator


class Deferrer:
    def __init__(self, remove_duplicates=False):
        self.deferrals = 0
        self.queue = []
        self.remove_duplicates = remove_duplicates

    def queue_command(self, f, args, kwargs):
        self.queue.append((f, args, kwargs))

    def defer(self):
        self.deferrals += 1

    def resume(self):
        assert self.deferrals > 0
        self.deferrals -= 1
        if self.deferrals > 0:
            return
        if self.remove_duplicates:
            queue = [k for k, _ in itertools.groupby(self.queue)]
        else:
            queue = self.queue
        try:
            for command in queue:
                command[0](*command[1], *command[2])
        finally:
            self.queue = []

    def __enter__(self):
        self.defer()

    def __exit__(self, *ex):
        self.resume()
        return False


def deferred_by_attribute(deferrer_name):
    def decorator(function):
        def wrapper(*args, **kwargs):
            self = args[0]
            deferrer = getattr(self, deferrer_name)
            if deferrer.deferrals > 0:
                deferrer.queue_command(function, args, kwargs)
            else:
                return function(*args, **kwargs)

        return wrapper

    return decorator


class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def lazy_property(getter):
    """Read-only property which is evaluated the first time it is accessed.
    
    The result is stored in an attribute with name prepended by an underscore. To
    clear the value, del the underscored name."""
    attr_name = '_' + getter.__name__

    @property
    def evaluate(self):
        try:
            value = getattr(self, attr_name)
        except AttributeError:
            value = getter(self)
            setattr(self, attr_name, value)
        return value

    return evaluate


def inplacemethod(func):
    """Mark an in-place (i.e. modifying its object) method as such, and add option to be not in-place."""

    def make(self, *args, inplace=True, **kwargs):
        if inplace:
            returned = func(self, *args, **kwargs)
            assert returned is None
            return
        else:
            result = copy.copy(self)
            returned = func(result, *args, **kwargs)
            assert returned is None
            return result

    return make


def coroutine(func):
    class Wrapper:
        def __init__(self, coroutine):
            self.coroutine = coroutine

        def send(self, value):
            try:
                self.coroutine.send(value)
            except StopIteration as e:
                return e.value

    def start(*args, prime=True, **kwargs):
        coroutine = func(*args, **kwargs)  # Create the coroutine (formally a generator)
        if prime:
            next(coroutine)  # Prime it
        return Wrapper(coroutine)

    return start


def accepts_evaluator(function):
    """Add evaluator argument to function.

    An evaluator is a callable which accepts a function and its arguments and returns the value of that function
    evaluated with those arguments. Obviously it also does something else that is useful - examples are caching, counting
    the number of times a function is called with particular arguments.

    One could of course decorate the function to perform the evaluator's job directly. Passing an evaluator offers more
    flexibility however.
    """

    def decorated(*args, evaluator=None, **kwargs):
        if evaluator is None:
            return function(*args, **kwargs)
        else:
            return evaluator(function, args, kwargs)

    return decorated
