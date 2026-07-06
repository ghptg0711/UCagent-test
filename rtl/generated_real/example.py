try:
    from UT_RealNutShellCache import *
except:
    try:
        from RealNutShellCache import *
    except:
        from __init__ import *


if __name__ == "__main__":
    dut = DUTRealNutShellCache()
    # dut.InitClock("clk")

    dut.Step(1)

    dut.Finish()
