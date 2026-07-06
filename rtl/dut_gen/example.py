try:
    from UT_NutShellCache import *
except:
    try:
        from NutShellCache import *
    except:
        from __init__ import *


if __name__ == "__main__":
    dut = DUTNutShellCache()
    # dut.InitClock("clk")

    dut.Step(1)

    dut.Finish()
