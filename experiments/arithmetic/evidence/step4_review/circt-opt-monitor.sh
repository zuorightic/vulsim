#!/bin/sh
printf "invoked\n" >> /home/zyrv/vulsim/build/step4-review/circt-invocations.log
exec /home/zyrv/circt/circt-full-shared-linux-x64/firtool-1.162.0/bin/circt-opt "$@"
