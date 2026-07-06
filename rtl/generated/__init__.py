#coding=utf8

try:
    from . import xspcomm as xsp
except Exception as e:
    import xspcomm as xsp

if __package__ or "." in __name__:
    from .libUT_NutShellCache import *
else:
    from libUT_NutShellCache import *





class DUTNutShellCache(object):

    # initialize
    def __init__(self, *args, **kwargs):
        self.dut = DutUnifiedBase(*args)
        self.xclock = xsp.XClock(self.dut.pxcStep, self.dut.pSelf)
        self.xport  = xsp.XPort()
        self.xclock.Add(self.xport)
        self.event = self.xclock.getEvent()
        self.internal_signals = {}
        self.xcfg = xsp.XSignalCFG(self.dut.GetXSignalCFGPath(), self.dut.GetXSignalCFGBasePtr())
        

        # set output files
        if kwargs.get("waveform_filename"):
            self.dut.SetWaveform(kwargs.get("waveform_filename"))
        if kwargs.get("coverage_filename"):
            self.dut.SetCoverage(kwargs.get("coverage_filename"))

        # All pins
        self.clock = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.reset = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.io_cpu_req_valid = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.io_cpu_req_ready = xsp.XPin(xsp.XData(0, xsp.XData.Out), self.event)
        self.io_cpu_req_bits_addr = xsp.XPin(xsp.XData(64, xsp.XData.In), self.event)
        self.io_cpu_req_bits_write = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.io_cpu_req_bits_wdata = xsp.XPin(xsp.XData(64, xsp.XData.In), self.event)
        self.io_cpu_req_bits_wmask = xsp.XPin(xsp.XData(8, xsp.XData.In), self.event)
        self.io_cpu_resp_valid = xsp.XPin(xsp.XData(0, xsp.XData.Out), self.event)
        self.io_cpu_resp_ready = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.io_cpu_resp_bits_data = xsp.XPin(xsp.XData(64, xsp.XData.Out), self.event)
        self.io_mem_req_valid = xsp.XPin(xsp.XData(0, xsp.XData.Out), self.event)
        self.io_mem_req_ready = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.io_mem_req_bits_addr = xsp.XPin(xsp.XData(64, xsp.XData.Out), self.event)
        self.io_mem_req_bits_write = xsp.XPin(xsp.XData(0, xsp.XData.Out), self.event)
        self.io_mem_req_bits_wdata = xsp.XPin(xsp.XData(512, xsp.XData.Out), self.event)
        self.io_mem_req_bits_wmask = xsp.XPin(xsp.XData(64, xsp.XData.Out), self.event)
        self.io_mem_resp_valid = xsp.XPin(xsp.XData(0, xsp.XData.In), self.event)
        self.io_mem_resp_ready = xsp.XPin(xsp.XData(0, xsp.XData.Out), self.event)
        self.io_mem_resp_bits_data = xsp.XPin(xsp.XData(512, xsp.XData.In), self.event)


        # BindDPI or Native pin address
        self.clock.BindDPIPtr(self.dut.GetDPIHandle("clock", 0), self.dut.GetDPIHandle("clock", 1))
        self.reset.BindDPIPtr(self.dut.GetDPIHandle("reset", 0), self.dut.GetDPIHandle("reset", 1))
        self.io_cpu_req_valid.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_req_valid", 0), self.dut.GetDPIHandle("io_cpu_req_valid", 1))
        self.io_cpu_req_ready.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_req_ready", 0), self.dut.GetDPIHandle("io_cpu_req_ready", 1))
        self.io_cpu_req_bits_addr.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_req_bits_addr", 0), self.dut.GetDPIHandle("io_cpu_req_bits_addr", 1))
        self.io_cpu_req_bits_write.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_req_bits_write", 0), self.dut.GetDPIHandle("io_cpu_req_bits_write", 1))
        self.io_cpu_req_bits_wdata.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_req_bits_wdata", 0), self.dut.GetDPIHandle("io_cpu_req_bits_wdata", 1))
        self.io_cpu_req_bits_wmask.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_req_bits_wmask", 0), self.dut.GetDPIHandle("io_cpu_req_bits_wmask", 1))
        self.io_cpu_resp_valid.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_resp_valid", 0), self.dut.GetDPIHandle("io_cpu_resp_valid", 1))
        self.io_cpu_resp_ready.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_resp_ready", 0), self.dut.GetDPIHandle("io_cpu_resp_ready", 1))
        self.io_cpu_resp_bits_data.BindDPIPtr(self.dut.GetDPIHandle("io_cpu_resp_bits_data", 0), self.dut.GetDPIHandle("io_cpu_resp_bits_data", 1))
        self.io_mem_req_valid.BindDPIPtr(self.dut.GetDPIHandle("io_mem_req_valid", 0), self.dut.GetDPIHandle("io_mem_req_valid", 1))
        self.io_mem_req_ready.BindDPIPtr(self.dut.GetDPIHandle("io_mem_req_ready", 0), self.dut.GetDPIHandle("io_mem_req_ready", 1))
        self.io_mem_req_bits_addr.BindDPIPtr(self.dut.GetDPIHandle("io_mem_req_bits_addr", 0), self.dut.GetDPIHandle("io_mem_req_bits_addr", 1))
        self.io_mem_req_bits_write.BindDPIPtr(self.dut.GetDPIHandle("io_mem_req_bits_write", 0), self.dut.GetDPIHandle("io_mem_req_bits_write", 1))
        self.io_mem_req_bits_wdata.BindDPIPtr(self.dut.GetDPIHandle("io_mem_req_bits_wdata", 0), self.dut.GetDPIHandle("io_mem_req_bits_wdata", 1))
        self.io_mem_req_bits_wmask.BindDPIPtr(self.dut.GetDPIHandle("io_mem_req_bits_wmask", 0), self.dut.GetDPIHandle("io_mem_req_bits_wmask", 1))
        self.io_mem_resp_valid.BindDPIPtr(self.dut.GetDPIHandle("io_mem_resp_valid", 0), self.dut.GetDPIHandle("io_mem_resp_valid", 1))
        self.io_mem_resp_ready.BindDPIPtr(self.dut.GetDPIHandle("io_mem_resp_ready", 0), self.dut.GetDPIHandle("io_mem_resp_ready", 1))
        self.io_mem_resp_bits_data.BindDPIPtr(self.dut.GetDPIHandle("io_mem_resp_bits_data", 0), self.dut.GetDPIHandle("io_mem_resp_bits_data", 1))


        # Add2Port
        self.xport.Add("clock", self.clock.xdata)
        self.xport.Add("reset", self.reset.xdata)
        self.xport.Add("io_cpu_req_valid", self.io_cpu_req_valid.xdata)
        self.xport.Add("io_cpu_req_ready", self.io_cpu_req_ready.xdata)
        self.xport.Add("io_cpu_req_bits_addr", self.io_cpu_req_bits_addr.xdata)
        self.xport.Add("io_cpu_req_bits_write", self.io_cpu_req_bits_write.xdata)
        self.xport.Add("io_cpu_req_bits_wdata", self.io_cpu_req_bits_wdata.xdata)
        self.xport.Add("io_cpu_req_bits_wmask", self.io_cpu_req_bits_wmask.xdata)
        self.xport.Add("io_cpu_resp_valid", self.io_cpu_resp_valid.xdata)
        self.xport.Add("io_cpu_resp_ready", self.io_cpu_resp_ready.xdata)
        self.xport.Add("io_cpu_resp_bits_data", self.io_cpu_resp_bits_data.xdata)
        self.xport.Add("io_mem_req_valid", self.io_mem_req_valid.xdata)
        self.xport.Add("io_mem_req_ready", self.io_mem_req_ready.xdata)
        self.xport.Add("io_mem_req_bits_addr", self.io_mem_req_bits_addr.xdata)
        self.xport.Add("io_mem_req_bits_write", self.io_mem_req_bits_write.xdata)
        self.xport.Add("io_mem_req_bits_wdata", self.io_mem_req_bits_wdata.xdata)
        self.xport.Add("io_mem_req_bits_wmask", self.io_mem_req_bits_wmask.xdata)
        self.xport.Add("io_mem_resp_valid", self.io_mem_resp_valid.xdata)
        self.xport.Add("io_mem_resp_ready", self.io_mem_resp_ready.xdata)
        self.xport.Add("io_mem_resp_bits_data", self.io_mem_resp_bits_data.xdata)


        # Cascaded ports
        self.io = self.xport.NewSubPort("io_")
        self.io_cpu = self.xport.NewSubPort("io_cpu_")
        self.io_cpu_req = self.xport.NewSubPort("io_cpu_req_")
        self.io_cpu_req_bits = self.xport.NewSubPort("io_cpu_req_bits_")
        self.io_cpu_resp = self.xport.NewSubPort("io_cpu_resp_")
        self.io_mem = self.xport.NewSubPort("io_mem_")
        self.io_mem_req = self.xport.NewSubPort("io_mem_req_")
        self.io_mem_req_bits = self.xport.NewSubPort("io_mem_req_bits_")
        self.io_mem_resp = self.xport.NewSubPort("io_mem_resp_")


    def __del__(self):
        self.Finish()

    ################################
    #         User APIs            #
    ################################
    def InitClock(self, name: str):
        self.xclock.Add(self.xport[name])

    def Step(self, i:int = 1):
        self.xclock.Step(i)

    def StepRis(self, callback, args=(), kwargs={}):
        self.xclock.StepRis(callback, args, kwargs)

    def StepFal(self, callback, args=(), kwargs={}):
        self.xclock.StepFal(callback, args, kwargs)

    def ResumeWaveformDump(self):
        return self.dut.ResumeWaveformDump()

    def PauseWaveformDump(self):
        return self.dut.PauseWaveformDump()

    def WaveformPaused(self) -> int:
        """ Returns 1 if waveform export is paused """
        return self.dut.WaveformPaused()

    def GetXPort(self):
        return self.xport

    def GetXClock(self):
        return self.xclock

    def SetWaveform(self, filename: str):
        self.dut.SetWaveform(filename)

    def GetWaveFormat(self) -> str:
        """
        Get the waveform extension, or an empty string if disabled.

        Returns:
            str: The extension of waveform file.
        """
        return self.dut.GetWaveFormat()

    def FlushWaveform(self):
        self.dut.FlushWaveform()

    def SetCoverage(self, filename: str):
        self.dut.SetCoverage(filename)

    def ResetCoverage(self):
        self.dut.ResetCoverage()

    def GetCovMetrics(self) -> int:
        """
        Get the bitmask for collected coverage metrics. 0 means coverage is disabled

        Returns:
            int: Collected coverage metrics bitmask:
                - Bit 0: line   (Line coverage)
                - Bit 1: cond   (Condition coverage)
                - Bit 2: fsm    (Finite-State Machine coverage)
                - Bit 3: toggle (Toggle coverage)
                - Bit 4: branch (Branch coverage)
                - Bit 5: assert (Assertion coverage)
        """
        return self.dut.GetCovMetrics()
    
    def CheckPoint(self, name: str) -> int:
        self.dut.CheckPoint(name)

    def Restore(self, name: str) -> int:
        self.dut.Restore(name)

    def GetInternalSignal(self, name: str, index=-1, is_array=False, use_vpi=False):
        if name not in self.internal_signals:
            signal = None
            if self.dut.GetXSignalCFGBasePtr() != 0 and not use_vpi:
                xname = "CFG:" + name
                if is_array:
                    assert index < 0, "Index is not supported for array signal"
                    signal = self.xcfg.NewXDataArray(name, xname)
                elif index >= 0:
                    signal = self.xcfg.NewXData(name, index, xname)
                else:
                    signal = self.xcfg.NewXData(name, xname)
            else:
                assert index < 0, "Index is not supported for VPI signal"
                assert not is_array, "Array is not supported for VPI signal"
                signal = xsp.XData.FromVPI(self.dut.GetVPIHandleObj(name),
                                           self.dut.GetVPIFuncPtr("vpi_get"),
                                           self.dut.GetVPIFuncPtr("vpi_get_value"),
                                           self.dut.GetVPIFuncPtr("vpi_put_value"), "VPI:" + name)
                if use_vpi:
                    assert signal is not None, f"Internal signal {name} not found (Check VPI is enabled)"
            if signal is None:
                return None
            if not isinstance(signal, xsp.XData):
                self.internal_signals[name] = [xsp.XPin(s, self.event) for s in signal]
            else:
                self.internal_signals[name] = xsp.XPin(signal, self.event)
        return self.internal_signals[name]

    def GetInternalSignalList(self, prefix="", deep=99, use_vpi=False):
        if self.dut.GetXSignalCFGBasePtr() != 0 and not use_vpi:
            return self.xcfg.GetSignalNames(prefix)
        else:
            return self.dut.VPIInternalSignalList(prefix, deep)

    def VPIInternalSignalList(self, prefix="", deep=99):
        return self.dut.VPIInternalSignalList(prefix, deep)

    def Finish(self):
        self.dut.Finish()

    def RefreshComb(self):
        self.dut.RefreshComb()

    def AtClone(self):
        """Re-init simulator state in child after fork."""
        return self.dut.atClone()

    ################################
    #      End of User APIs        #
    ################################

    def __getitem__(self, key):
        return xsp.XPin(self.port[key], self.event)

    # Async APIs wrapped from XClock
    async def AStep(self,i: int):
        return await self.xclock.AStep(i)

    async def ACondition(self,fc_cheker):
        return await self.xclock.ACondition(fc_cheker)

    def RunStep(self,i: int):
        return self.xclock.RunStep(i)

    def __setattr__(self, name, value):
        assert not isinstance(getattr(self, name, None),
                              (xsp.XPin, xsp.XData)), \
        f"XPin and XData of DUT are read-only, do you mean to set the value of the signal? please use `{name}.value = ` instead."
        return super().__setattr__(name, value)


if __name__=="__main__":
    dut=DUTNutShellCache()
    dut.Step(100)
