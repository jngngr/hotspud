import sys
import time
import logging
import shutil
import os
import subprocess
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from watchdog.events import RegexMatchingEventHandler
from watchdog.utils import has_attribute

class spudRegexMatchingEventHandler(RegexMatchingEventHandler):

    @property
    def in_path(self):
        return self._in_path

    @property
    def out_path(self):
        return self._out_path

    @property
    def proc_path(self):
        return self._proc_path

    @property
    def fail_path(self):
        return self._fail_path

    @property
    def proc_cmd(self):
        return self._proc_cmd

    @property
    def proc_timeout(self):
        return self._proc_timeout

    @in_path.setter
    def in_path(self, in_path):
        if(in_path.endswith("/")): 
            in_path = in_path[:-1]
        if(not os.path.exists(in_path)): 
            logging.info("input path %s created", in_path)
            os.makedirs(in_path)
        self._in_path = in_path

    @proc_path.setter
    def proc_path(self, proc_path):
        if(proc_path.endswith("/")): 
            proc_path = proc_path[:-1]
        if(not os.path.exists(proc_path)):
            logging.info("processing path %s created", proc_path)
            os.makedirs(proc_path)
        self._proc_path = proc_path

    @out_path.setter
    def out_path(self, out_path):
        if(out_path.endswith("/")): 
            out_path = out_path[:-1]
        if(not os.path.exists(out_path)):
            logging.info("output path %s created", out_path)
            os.makedirs(out_path)
        self._out_path = out_path

    @fail_path.setter
    def fail_path(self, fail_path):
        if(fail_path.endswith("/")): 
            fail_path = fail_path[:-1]
        if(not os.path.exists(fail_path)):
            logging.info("fail path %s created", fail_path)
            os.makedirs(fail_path)
        self._fail_path = fail_path

    @proc_cmd.setter
    def proc_cmd(self, proc_cmd):
        if(proc_cmd != ""):
            if(not (os.path.isfile(proc_cmd) and os.access(proc_cmd, os.X_OK))):
                logging.critical("command %s not found or is not executable", proc_cmd)
                quit()
        self._proc_cmd = proc_cmd

    @proc_timeout.setter
    def proc_timeout(self, proc_timeout):
        self._proc_timeout = proc_timeout

    def on_any_event(self, event):
        if(event.event_type == 'deleted'): return
        if(event.src_path == self.in_path): return
        logging.debug("event %s for %s", event.event_type, event.src_path)
        self.process(event)

    def process(self, event):
        item_path = event.dest_path if(has_attribute(event,'dest_path')) else event.src_path
        item_name = item_path.replace(self.in_path + "/", "")
        item_proc_path = item_path.replace(self.in_path, self.proc_path)
        item_out_path = item_path.replace(self.in_path, self.out_path)
        item_fail_path = item_path.replace(self.in_path, self.fail_path)
        logging.info("found item %s", item_path)
        if(self.proc_cmd != ""):
            proc_cmd = []
            proc_cmd.append(self.proc_cmd)
            proc_cmd.append(item_name)
            shutil.move(item_path, item_proc_path)
            logging.debug("item %s moved to processing path %s", item_path, item_proc_path)
            try:
                logging.info("running command %s %s in folder %s", self.proc_cmd, item_name, self.proc_path)
                subprocess.run(args=proc_cmd, cwd=self.proc_path, check=True, timeout=self.proc_timeout)
                logging.debug("command finished")
                if(os.path.exists(item_proc_path)): 
                    shutil.move(item_proc_path, item_out_path)
                    logging.info("item %s moved to output path %s", item_name, item_out_path)
                else:
                    logging.error("item %s not found in process path %s after command execution", item_name, self.proc_path)
            except subprocess.CalledProcessError as e:
                logging.error("command %s encountered an error.\nReturn code: %s\nSTDERR: %s", e.cmd, e.returncode, e.stderr)
                if(os.path.exists(item_proc_path)): 
                    shutil.move(item_proc_path, item_fail_path)
                    logging.info("item %s moved to fail path %s", item_name, item_fail_path)
            except subprocess.TimeoutExpired as e:
                logging.error("command %s timed-out after %i seconds", e.cmd, e.timeout)
                if(os.path.exists(item_proc_path)): 
                    shutil.move(item_proc_path, item_fail_path)
                    logging.info("item %s moved to fail path %s", item_name, item_fail_path)
            except:
                logging.error("command %s encountered an error", e.cmd)
                if(os.path.exists(item_proc_path)): 
                    shutil.move(item_proc_path, item_fail_path)
                    logging.info("item %s moved to fail path %s", item_name, item_fail_path)
        else:
                shutil.move(item_path, item_out_path)
                logging.info("item %s moved to output path %s", item_path, item_out_path)

    def __init__(self, regexes=[r".*"], 
            ignore_regexes=[], 
            ignore_directories=False, 
            case_sensitive=False, 
            in_path=(str(Path.home())+"/in"), 
            out_path=(str(Path.home())+"/out"), 
            fail_path=(str(Path.home())+"/fail"), 
            proc_path=(str(Path.home())+"/proc"), 
            proc_cmd="",
            proc_timeout=None):
        super(spudRegexMatchingEventHandler, self).__init__(regexes, ignore_regexes, ignore_directories, case_sensitive)
        self.in_path = in_path
        self.out_path = out_path
        self.proc_path = proc_path
        self.proc_cmd = proc_cmd
        self.proc_timeout = proc_timeout
        self.fail_path = fail_path

if __name__ == "__main__":
    # Get settings from ENV
    log_level_str = os.getenv('HOTSPUD_LOG_LEVEL')
    regex_str = os.getenv('HOTSPUD_REGEX')
    ignore_regex_str = os.getenv('HOTSPUD_IGNORE_REGEX')
    path_in = os.getenv('HOTSPUD_PATH_IN')
    path_out = os.getenv('HOTSPUD_PATH_OUT')
    path_proc = os.getenv('HOTSPUD_PATH_PROC')
    path_fail = os.getenv('HOTSPUD_PATH_FAIL')
    cmd_proc = os.getenv('HOTSPUD_PROC_CMD')
    timeout_proc_str = os.getenv('HOTSPUD_PROC_TIMEOUT')
    poll_period_str = os.getenv('HOTSPUD_PERIOD')

    # this is going to be brute force...
    if(log_level_str == "CRITICAL"):
        log_level=logging.CRITICAL
    elif(log_level_str == "ERROR"):
        log_level=logging.ERROR
    elif(log_level_str == "WARNING"):
        log_level=logging.WARNING
    elif(log_level_str == "DEBUG"):
        log_level=logging.DEBUG
    else:
        # this includes the case wherein there's no ENV variable
        log_level=logging.INFO
    if(regex_str == None): 
        regex_arr = [r".*"]
    else: 
        regex_arr = []
        regex_arr.append(regex_str)
    ignore_regex_arr = []
    if(ignore_regex_str != None): 
        ignore_regex_arr.append(ignore_regex_str)
    poll_period = 15 if(poll_period_str == None) else int(poll_period_str)
    timeout_proc = None if(timeout_proc_str == None) else int(timeout_proc_str)+1
    if(path_in == None): path_in=(str(Path.home())+"/in")
    if(path_out == None): path_out=(str(Path.home())+"/out")
    if(path_proc == None): path_proc=(str(Path.home())+"/proc")
    if(cmd_proc == None): cmd_proc=""
    if(path_fail == None): path_fail=(str(Path.home())+"/fail")

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    event_handler = spudRegexMatchingEventHandler(regexes=regex_arr, 
            ignore_regexes=ignore_regex_arr,
            ignore_directories=False,
            in_path=path_in,
            proc_path=path_proc,
            out_path=path_out,
            proc_cmd=cmd_proc,
            proc_timeout=timeout_proc)

    observer = PollingObserver(timeout=poll_period)
    observer.schedule(event_handler, path_in, recursive=False)
    observer.start()
    logging.info("started")
    logging.info("input path      : \"%s\"", path_in)
    logging.info("output path     : \"%s\"", path_out)
    logging.info("process path    : \"%s\"", path_proc)
    logging.info("fail path       : \"%s\"", path_fail)
    logging.info("process command : \"%s\"", cmd_proc)
    logging.info("process timeout : \"%s\"", timeout_proc)
    logging.info("poll period     : \"%i\"", poll_period)
    logging.info("regex           : \"%s\"", ",".join(regex_arr))
    logging.info("ignore_regex    : \"%s\"", ",".join(ignore_regex_arr))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
