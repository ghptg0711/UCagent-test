#!/usr/bin/env bash
set -euo pipefail

UCAGENT=/mnt/d/UCagent
NUTSHELL="$UCAGENT/NutShell"

cd "$NUTSHELL"

export NOOP_HOME="$NUTSHELL"
export MILL_JVM_OPTS=-Xmx4G
MILL=/home/gh0711/.cache/mill/download/0.11.7

git -c http.version=HTTP/1.1 submodule update --init --force --depth=1 difftest

env NOOP_HOME="$NOOP_HOME" MILL_JVM_OPTS="$MILL_JVM_OPTS" \
  "$MILL" --no-server --disable-ticker generator.compile

env NOOP_HOME="$NOOP_HOME" MILL_JVM_OPTS="$MILL_JVM_OPTS" \
  "$MILL" --no-server --disable-ticker show generator.runClasspath >/tmp/nutshell_generator_runclasspath.json

rm -rf out/manual-realcache
mkdir -p out/manual-realcache/classes

CP=$(python3 - <<'PY'
import json
items = json.load(open("out/generator/runClasspath.json"))["value"]
paths = []
for item in items:
    path = item.split(":", 3)[-1] if item.startswith(("qref:", "ref:")) else item
    paths.append(path)
print(":".join(paths))
PY
)

COMPILER=/home/gh0711/.cache/coursier/v1/https/repo1.maven.org/maven2/org/scala-lang/scala-compiler/2.13.14/scala-compiler-2.13.14.jar
LIBRARY=/home/gh0711/.cache/coursier/v1/https/repo1.maven.org/maven2/org/scala-lang/scala-library/2.13.14/scala-library-2.13.14.jar
REFLECT=/home/gh0711/.cache/coursier/v1/https/repo1.maven.org/maven2/org/scala-lang/scala-reflect/2.13.14/scala-reflect-2.13.14.jar
PLUGIN=/home/gh0711/.cache/coursier/v1/https/repo1.maven.org/maven2/org/chipsalliance/chisel-plugin_2.13.14/7.11.0/chisel-plugin_2.13.14-7.11.0.jar

java -cp "$COMPILER:$LIBRARY:$REFLECT" scala.tools.nsc.Main \
  -cp "$CP" \
  -d out/manual-realcache/classes \
  -Xplugin:"$PLUGIN" \
  -Ymacro-annotations \
  "$UCAGENT/tools/RealCacheMain.scala"

rm -rf build/cache_rtl
mkdir -p build/cache_rtl

java -cp "out/manual-realcache/classes:$CP" top.RealCacheMain \
  --target-dir "$NUTSHELL/build/cache_rtl" \
  --split-verilog

find build/cache_rtl -maxdepth 1 -type f | sort
