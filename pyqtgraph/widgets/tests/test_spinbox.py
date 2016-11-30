import pyqtgraph as pg
pg.mkQApp()

def test_spinbox():
    sb = pg.SpinBox()
    assert sb.opts['decimals'] == 3
    assert sb.opts['int'] is False
    
    # table  of test conditions:
    # value, text, options
    conds = [
        (0, '0', dict(suffix='', siPrefix=False, dec=False, int=False)),
        (100, '100', dict()),
        (1000000, '1e+06', dict()),
        (1000, '1e+03', dict(decimals=2)),
        (1000000, '1000000', dict(int=True)),
        (12345678955, '12345678955', dict(int=True)),
    ]
    
    for (value, text, opts) in conds:
        sb.setOpts(**opts)
        sb.setValue(value)
        assert sb.value() == value
        assert pg.asUnicode(sb.text()) == text
