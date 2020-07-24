#!/bin/bash
TARGET=$1

# Note: most logging should be done by your process command
LOGFILE="$(dirname $0)/log.txt"

if [ -d "$TARGET" ]; then
	echo "item is a folder" | tee -a $LOGFILE
	touch ${TARGET}/sample.txt
else
	echo "item is a file" | tee -a $LOGFILE
	echo "hello there" >> $TARGET
fi
