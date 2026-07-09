#!/usr/bin/env bash
set -euo pipefail

cd /mnt/d/UCagent/NutShell

export NOOP_HOME=/mnt/d/UCagent/NutShell
export MILL_JVM_OPTS=-Xmx4G

git -c http.version=HTTP/1.1 submodule update --init --force --depth=1 difftest

env NOOP_HOME="$NOOP_HOME" MILL_JVM_OPTS="$MILL_JVM_OPTS" \
  mill --no-server --disable-ticker generator.compile

env NOOP_HOME="$NOOP_HOME" MILL_JVM_OPTS="$MILL_JVM_OPTS" \
  mill --no-server --disable-ticker show generator.test.runClasspath >/tmp/nutshell_runclasspath.json

rm -rf out/manual-topmain
mkdir -p out/manual-topmain/classes

CP=$(python3 - <<'PY'
import json
items = json.load(open("out/generator/test/runClasspath.json"))["value"]
paths = []
for item in items:
    path = item.split(":", 3)[-1] if item.startswith(("qref:", "ref:")) else item
    if "out/generator/test/compile.dest/classes" not in path:
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
  -d out/manual-topmain/classes \
  -Xplugin:"$PLUGIN" \
  -Ymacro-annotations \
  src/test/scala/TopMain.scala

rm -rf build/rtl
mkdir -p build/rtl

java -cp "out/manual-topmain/classes:$CP" top.TopMain \
  --target-dir /mnt/d/UCagent/NutShell/build/rtl \
  BOARD=sim \
  CORE=inorder \
  --split-verilog

find build/rtl -maxdepth 1 -type f | sort
