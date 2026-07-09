package top

import chisel3._
import chisel3.util.experimental.BoringUtils
import chisel3.stage.ChiselGeneratorAnnotation
import circt.stage._
import nutcore.{Cache, CacheConfig, CacheIO}

class RealNutShellCache(implicit val cacheConfig: CacheConfig) extends Module {
  override def desiredName: String = "RealNutShellCache"

  val io = IO(new CacheIO)
  val cache = Module(new Cache)
  io <> cache.io

  val lsuMMIO = WireInit(false.B)
  BoringUtils.addSink(lsuMMIO, "lsuMMIO")
  dontTouch(lsuMMIO)
}

object RealCacheMain extends App {
  Settings.settings = DefaultSettings() ++ InOrderSettings()

  val cacheConfig = CacheConfig(
    ro = false,
    name = "dcache",
    userBits = 16,
    idBits = 0,
    cacheLevel = 1,
    totalSize = 32,
    ways = 4
  )

  (new ChiselStage).execute(
    args,
    Seq(
      ChiselGeneratorAnnotation(() => new RealNutShellCache()(cacheConfig)),
      CIRCTTargetAnnotation(CIRCTTarget.SystemVerilog),
      FirtoolOption("--disable-annotation-unknown"),
      FirtoolOption("--default-layer-specialization=enable")
    )
  )
}
