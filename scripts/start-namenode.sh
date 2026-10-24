#!/usr/bin/env bash
set -euo pipefail
if [ ! -f /data/namenode/current/VERSION ]; then
  echo 'Formatting fresh classroom NameNode storage (first start only).'
  hdfs namenode -format -nonInteractive
fi
exec hdfs namenode
