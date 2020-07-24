# hotspud

Move files or folders (hereon referred to simply as "items") between input and output paths, optionally running a script during the process.

## TL;DR

### Simple usage

The example below simply moves items from an input to an output folder.

```
IN_FOLDER=/mount/dropbox
OUT_FOLDER=/mount/storage
sudo docker run \
    --rm \
    -d \
    --name simple \
    -v ${IN_FOLDER}:/root/in \
    -v ${OUT_FOLDER}:/root/out \
    jngngr/hotspud:latest
```

### Less Simple usage

The example below moves items from an input to an output folder but runs a script against each item.

```
IN_FOLDER=/mount/fs1/dropbox
OUT_FOLDER=/mount/fs2/storage
PROC_FOLDER=/mount/fs2/staging
FAIL_FOLDER=/mount/fs2/fail
SCRIPT=/home/user/script.sh
sudo docker run \
    --rm \
    -d \
    --name lesssimple \
    -v ${IN_FOLDER}:/root/in \
    -v ${OUT_FOLDER}:/root/out \
    -v ${PROC_FOLDER}:/root/proc \
    -v ${FAIL_FOLDER}:/root/fail \
    -v ${SCRIPT}:/script.sh \
    -e HOTSPUD_PROC_CMD=/script.sh \
    jngngr/hotspud:latest
```

## Details

This makes use of the excellent [watchdog Python library](https://github.com/gorakhargosh/watchdog).

### Process

```plantuml
(*) --> "detect input item"
if "script given?" then
    --> [yes] "move item to process path"
    --> "run script"
    if "error encountered"
       --> [yes] "move item to fail path"
       --> (*)
    else
       --> "move item to destination path"
    endif
else
    --> "move item to destination path"
endif
--> (*)
```

### Configuration options

All settings are controlled using environment variables.

Variable             | Default/Unset value | Description
-------------------- | ------------------- | -----------------------------------------------------------------------------------------------------------------------
HOTSPUD_LOG_LEVEL    | INFO                | Logging level. Valid values: CRITICAL, ERROR, WARNING, DEBUG, INFO
HOTSPUD_REGEX        | .*                  | Regular expression for matching accepted files
HOTSPUD_IGNORE_REGEX |                     | Regular expression for matching blocked files
HOTSPUD_PATH_IN      | /root/in            | Path for incoming files
HOTSPUD_PATH_OUT     | /root/out           | Destination path
HOTSPUD_PROC_CMD     |                     | Script to run on files before they are moved to the destination path. Script must have exec bit set.
HOTSPUD_PATH_PROC    | /root/proc          | Folder where the script will be run
HOTSPUD_PATH_FAIL    | /root/fail          | Files that trigger a script failure will be moved here
HOTSPUD_PROC_TIMEOUT | None                | Maximum time (in sec) the specified script can run
HOTSPUD_PERIOD       | 15                  | Polling time for checking arrival of new files. Increase this according to the size of files that will be moved around.

### Notes on the processing script

1. The processing script will be invoked with only the name of the current item as a parameter. The item will be in the path specified by `HOTSPUD_PATH_PROC`. The script should not rename or otherwise remove the item from this location. The item should exist in this location after the script finishes execution. If your use case requires generating new files or renaming files, it would be best to use folders with the actual input files for the script contained within them as items.
2. The script should provide detailed log information if you require such.
3. The script should do any required "housekeeping" activities or else `HOTSPUD_PATH_PROC` may fill up.
4. The base image used is ubuntu:20.10\. You'll have to modify this image if you require more tools than what is available in ubuntu:20.10.
5. A sample script is provided in the "/hotspud" folder.
