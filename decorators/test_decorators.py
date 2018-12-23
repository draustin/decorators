from decorators import *

def test_Deferrer():
    class X:
        def __init__(self):
            self.deferrer = Deferrer()
            self.times_done = 0

        @deferred_by_attribute('deferrer')
        def doit(self):
            self.times_done += 1

    x = X()
    x.doit()
    assert x.times_done == 1
    x.deferrer.defer()
    assert x.times_done == 1
    x.doit()
    x.doit()
    assert x.times_done == 1
    x.deferrer.resume()
    assert x.times_done == 3

    with x.deferrer:
        assert x.times_done == 3
        x.doit()
        x.doit()
        assert x.times_done == 3
    assert x.times_done == 5
    x.doit()
    assert x.times_done == 6

    x.deferrer.remove_duplicates = True
    with x.deferrer:
        x.doit()
        x.doit()
        assert x.times_done == 6
    assert x.times_done == 7


def test_inplace():
    class HasX:
        def __init__(self):
            self.x = 0

        @inplacemethod
        def increment_x(self, by=1):
            self.x += by

    hasx = HasX()
    hasx.increment_x()
    assert hasx.x == 1
    hasx2 = hasx.increment_x(inplace=False)
    assert hasx2.x == 2
    assert hasx.x == 1
