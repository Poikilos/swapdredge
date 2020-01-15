#!/usr/env python
import os
import sys
import codecs
from datetime import datetime
import shutil
import imghdr
import tempfile
import math

SEPARATOR = """
-------------
  Separator
-------------
"""
# My biggest py file is 224K (~/git/yofrankie-install/
# blender-2.49a-linux-glibc236-py26-x86_64/.blender/scripts/
# import_dxf.py), but adjust BACKTRACK_MAX as necessary for code
# or other recognizable data:
BACKTRACK_MAX = 400*1024*1024

dump_prefix = "swapdredge"
def mkdir_dated(where, now_s=None, unique=True):
    today_s = datetime.today().strftime('%Y-%m-%d')
    if now_s is None:
        now_s = datetime.now().strftime('%Y-%m-%d_%H..%M..%S')
    initial_this_dir_s = dump_prefix + "_" + now_s
    this_dir_s = initial_this_dir_s
    dir_i = 1
    this_dir_path = os.path.join(where, this_dir_s)
    if unique:
        while os.path.isdir(this_dir_path):
            this_dir_s = initial_this_dir_s + "#" + str(dir_i)
            this_dir_path = os.path.join(where, this_dir_s)
            dir_i += 1
    if not os.path.isdir(this_dir_path):  # always True if unique
        os.mkdir(this_dir_path)
    return this_dir_path

commands = ['find', 'dump']
command_reqs = {}
command_reqs['dump'] = ['start', 'length']

openers = {}
# See http://dcjtech.info/topic/list-of-shebang-interpreter-directives/
openers["sh"] = [b"#!/bin/bash", b"#!/bin/sh", b"#!/usr/bin/env sh",
                 b"#!/usr/bin/env bash", b"#!/bin/cat",
                 b"#!/usr/bin/awk", b"#!/bin/ash", b"#!/bin/csh",
                 b"#!/bin/busybox", b"#!/bin/sed ", b"#!/usr/bin/sed ",
                 b"#!/usr/bin/env sed", b"#!/usr/xpg4/bin/sh",
                 b"#!/bin/tcsh"]
openers["groovy"] = [b"#!/usr/local/bin/groovy",
                     b"#!/usr/bin/env groovy"]
openers["js"] = [b"#!/usr/bin/env jsc", b"#!/usr/bin/env node",
                 b"#!/usr/bin/env rhino"]
openers["lsp"] = [b"#!/usr/local/bin/sbcl"]
openers["lua"] = [b"#!/usr/bin/env lua", b"#!/usr/bin/lua"]
openers["makefile"] = [b"#!/usr/bin/make"]  # makefile: usually fullname
openers["pl"] = [b"#!/usr/bin/env perl", b"#!/usr/bin/perl"]
openers["php"] = [b"#!/usr/bin/php", b"#!/usr/bin/env php"]
openers["py"] = [b"#!/usr/bin/env python"] # ends with 2, 3, or 3.4 etc
openers["ruby"] = [b"#!/usr/bin/env ruby", b"#!/usr/bin/ruby"]

_BANG_MAX = 0

BOMs = [chr(255) + chr(254), chr(254) + chr(255)]

for k, flags in openers.items():
    for flag in flags:
        if len(flag) > _BANG_MAX:
            _BANG_MAX = len(flag)

def s_to_bytes(s):
    return s.encode()  # utf-8 is default in Python3; no param is faster

def get_type_at(s):
    # if s[:2] in BOMs:  # rare, and inconclusive
        # return True
    for k, flags in openers.items():
        for flag in flags:
            if s.startswith(flag):
                return k
    return None

config = {}
config['preview_show_before'] = 512
config['preview_show_after'] = 512
config_help = {}
config_help['find'] = (
    "what word (or phrase in quotes) to find in the file (required)"
)
config_help['dump'] = (
    "Dump part of the input to to standard output."
    "Normally you would do this using any numbers from results,"
    "\n  or subtract to see further back in the file."
    "\n  Requires:"
    "\n  --start <byte_index>"
    "\n  --length <byte_count>"
)
bad_chars = []



def c_to_hex(c):
    ret = None
    try:
        ret = c.encode("hex")
    except LookupError:
        ret = codecs.encode(c.encode(), "hex")
    return ret


for i in range(256):
    good_control_chars = [9, 10, 13]  # Not bad:
    # 9 is tab (displayable)
    # 10 is line feed (displayable)
    # 13 is carriage return (displayable)
    if i == 0:
        bad_chars.append("null")
    elif i == 127:
        bad_chars.append("delete")
    elif (i < 32) and (i not in good_control_chars):
        bad_char_hex = c_to_hex(chr(i))
        s = "control character {} (0x{})".format(
            i,
            bad_char_hex
        )
        # print(s)
        bad_chars.append(s)
    elif i == 254:
        bad_chars.append("0xFE such as second part of BOM")
    elif i == 255:
        bad_chars.append("DEL or memory fill 1 such as 2nd part of BOM")
        # NOTE: UTF bytes would be ordered such that the output is FEFF
    else:
        bad_chars.append(None)


control_descriptions = {}
# See https://www.asciitable.xyz/
control_descriptions["NUL"] = "null character"
control_descriptions["SOH"] = "start of header"
control_descriptions["STX"] = "start of text"
control_descriptions["ETX"] = "end of text"
control_descriptions["EOT"] = "end of transmission"
control_descriptions["ENQ"] = "enquiry"
control_descriptions["ACK"] = "acknowledge"
control_descriptions["BEL"] = "bell ring"
control_descriptions["BS"] = "backspace"
control_descriptions["HT"] = "horizontal tab"
control_descriptions["LF"] = "line feed"
control_descriptions["VT"] = "vertical tab"
control_descriptions["FF"] = "form feed"
control_descriptions["CR"] = "carriage return"
control_descriptions["SO"] = "shift out"
control_descriptions["SI"] = "shift in"
control_descriptions["DLE"] = "data link escape"
control_descriptions["DC1"] = "device control 1"
control_descriptions["DC2"] = "device control 2"
control_descriptions["DC3"] = "device control 3"
control_descriptions["DC4"] = "device control 4"
control_descriptions["NAK"] = "negative acknowledgement"
control_descriptions["SYN"] = "synchronize"
control_descriptions["ETB"] = "end transmission block"
control_descriptions["CAN"] = "cancel"
control_descriptions["EM"] = "end of medium"
control_descriptions["SUB"] = "substitute"
control_descriptions["ESC"] = "escape"
control_descriptions["FS"] = "file separator"
control_descriptions["GS"] = "group separator"
control_descriptions["RS"] = "record separator"
control_descriptions["US"] = "unit separator"
bad_chars[0] = "NUL"
bad_chars[1] = "SOH"
bad_chars[2] = "STX"
bad_chars[3] = "ETX"
bad_chars[4] = "EOT"
bad_chars[5] = "ENQ"
bad_chars[6] = "ACK"
bad_chars[7] = "BEL"
bad_chars[8] = "BS"
# bad_chars[9] = "HT"  # ok since displayable (tab)
# bad_chars[10] = "LF"  # ok since displayable (after CR on Windows)
bad_chars[11] = "VT"
bad_chars[12] = "FF"
# bad_chars[13] = "CR"  #ok since displayable
bad_chars[14] = "SO"
bad_chars[15] = "SI"
bad_chars[16] = "DLE"
bad_chars[17] = "DC1"
bad_chars[18] = "DC2"
bad_chars[19] = "DC3"
bad_chars[20] = "DC4"
bad_chars[21] = "NAK"
bad_chars[22] = "SYN"
bad_chars[23] = "ETB"
bad_chars[24] = "CAN"
bad_chars[25] = "EM"
bad_chars[26] = "SUB"
bad_chars[27] = "ESC"
bad_chars[28] = "FS"
bad_chars[29] = "GS"
bad_chars[30] = "RS"
bad_chars[31] = "US"
for x in range(32):
    if bad_chars[x] is not None:
        try:
            d = control_descriptions[bad_chars[x]]
        except KeyError:
            raise RuntimeError("The control_descriptions are not"
                               " complete ({}".format(bad_chars[x])
                               + " is missing)."
                               " This version is broken.")


config_help['preview_show_before'] = (
    "bytes to show before result upon find (default:"
    + str(config['preview_show_before']) + ")"
)
config_help['preview_show_after'] = (
    "bytes to show before result upon find (default:"
    + str(config['preview_show_after']) + ")"
)
config_help['skip'] = (
    "a count of bytes to skip before starting the search"
)
config_help['end'] = (
    "where in the file to stop searching (exclusive, and relative to"
    " the start of the file)"
)

def error(msg):
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

def customDie(msg, error_code=1):
    error("")
    error("ERROR:")
    error(msg)
    error("")
    error("")
    exit(error_code)

def usage():
    error("")
    error("==================== Usage ====================")
    error("Params are normally followed by space (but can be followed"
          " by equal sign instead if value has no spaces nor quotes)"
          " then a value.")
    error("Params:")
    for k, v in config_help.items():
        error("--" + k)
        error("  " + v)
    error("")
    error("Example:")
    error("python " + sys.argv[0] + ' image.dd --find "a phrase" > swapdredge_results.txt')
    error("#(The progress would still go to stderr so that you can see it while " + sys.argv[0] + " writes to stdout, which is results.txt in the example above).")
    error("")

progress_w = 40
progress_title = ""
# progress bar functions by 6502 on
# <https://stackoverflow.com/questions/6169217/\
# replace-console-output-in-python>
def startProgress(title):
    global progress_x
    global progress_title
    progress_title = title
    sys.stderr.write(title + ": [" + "-"*progress_w + "]" + "\r")
    #  chr(8)*41 is the same as "\r" (return, but not newline)
    sys.stderr.flush()
    progress_x = 0


def progress(x):
    global progress_x
    done_msg = "{0:.1f}%".format(x*100.0)
    if x > 1.0:
        x = 1.0
    # x = int(x * progress_w // 100)
    done = int(x * progress_w)
    remaining = progress_w - done
    sys.stderr.write("\r" + progress_title + ": [" + "#"*done + "-"*remaining + "] " + done_msg)
    # sys.stderr.write("#" * (done - progress_x))
    sys.stderr.flush()
    progress_x = done


def endProgress():
    sys.stderr.write("#" * (progress_w - progress_x) + "]\n")
    sys.stderr.flush()

def get_bad_index(c):
    ret = None
    c_index = ord(c)
    # # if c == '\0':
        # # ret = 0
    # # elif ord(c) == 255:
        # # ret = 255
    if bad_chars[c_index] is not None:
        ret = c_index
    return ret

def split_by_bad(txt):
    results = []
    result = b""
    for i in range(len(txt)):
        c = txt[i]
        if get_bad_index(c) is not None:
            if len(result) > 0:
                results.append(result)
                result = b""
        else:
            result += c
    if len(result) > 0:
        results.append(result)
    return results


def split_by_starters(txt):
    results = []
    result = b""
    for i in range(len(txt)):
        c = txt[i]
        t = get_type_at(txt[i:_BANG_MAX])
        if t is not None:
            if len(result) > 0:
                results.append(result)
                result = b""
        else:
            if txt[i:2] == b"#!":
                error("* unknown shebang '{}'".format(txt[i:_BANG_MAX]))
            result += c
    if len(result) > 0:
        results.append(result)
    return results

def main():
    paths = []
    name = None
    command = None
    good_start = None

    for argi in range(1, len(sys.argv)):
        # 0 is self
        arg = sys.argv[argi]
        if arg[:2] == "--":
            sign_i = arg.find("=")
            if sign_i > -1:
                config[arg[2:sign_i].strip()] = arg[sign_i+1:].strip()
                name = None
            else:
                if name is not None:
                    config[name] = True
                    name = arg[2:]
                else:
                    name = arg[2:].strip()
        else:
            if name is not None:
                config[name] = arg
            else:
                paths.append(arg.strip())
            name = None
    print("# config: " + str(config))
    print("# paths: " + str(paths))
    did_command = 0
    did_params = True
    for this_command in commands:
        if config.get(this_command) is not None:
            did_command += 1
            command = this_command
            reqs = command_reqs.get(this_command)
            if reqs is not None:
                did_params = True
                for req in reqs:
                    if req not in config:
                        did_params = False
                        error(this_command + " requires: " + req)
            else:
                did_params = True
    if did_command != 1:
        usage()
        error("")
        error("Nothing done since must specify one command:")
        for this_command in commands:
            error("  --" + this_command)
        error("")
        exit(1)
    elif not did_params:
        usage()
        customDie("You must specify the file path and required params"
                  "\n  (See \"Usage\" above).")

    piece_size = 1
    needle_i = 0
    needle = config.get("find")
    results = []
    before_s = ""
    before = config['preview_show_before']
    after = config['preview_show_after']
    after_s = None
    processed_mb = 0
    current_path = None
    total_mb = None
    rel_byte_i = None
    dump_s = None
    last_bad_index = None
    bad_index = None
    byte_i = 0  # changed to long if Python 2 (declare here for scope)
    now_s = datetime.now().strftime('%Y-%m-%d_%H..%M..%S')
    this_found_count = 0
    split_by_bang_path = None
    this_good_count_total = 0
    try:
        for path_i in range(len(paths)):

            path = paths[path_i]
            #total = os.path.getsize(path)
            if not os.path.isfile(path):
                error("ERROR: no file named '" + path + "'")
                continue
            current_path = path
            total = os.stat(path).st_size
            total_f = float(total)
            total_mb = int(os.stat(path).st_size / 1024 / 1024)
            total_mb_f = float(total_mb)
            rel_mb_byte_i = 0
            processed_mb = 0
            byte_i = 0
            try:
                byte_i = long(0)
            except NameError:
                pass  # already stored long since same as int in Python 3

            startProgress(path + " progress")
            buf = b""
            bufstart = 0
            try:
                bufstart = long(bufstart)
            except NameError:
                # Python 3 is always long.
                pass
            last_opener_i = None
            last_opener_type = None
            with open(path, 'rb') as ins:
                if command == "find":
                    skip = config.get("skip")
                    end = config.get("end")
                    if end is not None:
                        try:
                            end = long(end)
                        except NameError:
                            # Python 3 is always long.
                            end = int(end)

                    if skip is not None:
                        try:
                            skip = long(skip)
                        except NameError:
                            # Python 3 is always long.
                            skip = int(skip)
                        # error("* Seeking to {}...".format(skip))
                        ins.seek(skip) # 2nd param: 0(default): absolute
                        byte_i += skip
                        rel_mb_byte_i += skip
                        while rel_mb_byte_i >= 1048576:
                            rel_mb_byte_i -= 1048576
                            processed_mb += 1
                        # error("  OK.")
                        if end is not None:
                            progress(float(math.floor(byte_i/1024)) / float(math.ceil(end/1024)))
                        else:
                            progress(float(processed_mb) / total_mb_f)
                    while True:
                        if end is not None:
                            if byte_i >= end:
                                error("* The processing ended early"
                                      " since the user specified the"
                                      " end byte ('--end' setting).")
                                break
                        piece = ins.read(piece_size)
                        if piece == b"":
                            break  # EOF
                        buf += piece
                        if len(buf) > BACKTRACK_MAX:
                            cut_count = len(buf) - BACKTRACK_MAX
                            buf = buf[cut_count:]
                            bufstart += cut_count

                        # This fastest method only works if piece_size
                        # is 1:
                        if piece_size != 1:
                            raise RuntimeError("The piece_size is not 1"
                                               ", so file detection on"
                                               " every substring of the"
                                               " buffer must be"
                                               " implemented here.")
                        last_opener_type = get_type_at(buf)
                        if last_opener_type is not None:
                            last_opener_i = bufstart
                            print("* There is a(n) '{}' at {}".format(last_opener_type, bufstart))
                        elif buf[:2] == b"#!":
                            print("* There is an unknown shebang '{}' at {}".format(buf[:_BANG_MAX], bufstart))
                        if after_s is not None:
                            # decode("utf-8") fails (invalid start byte)
                            # after_s += piece.decode("utf-8")
                            after_s += piece
                            if len(after_s) >= after:
                                print(before_s+after_s)
                                after_s = None
                                before_s = ""
                        else:
                            # decode("utf-8") fails (invalid start byte)
                            # before_s += piece.decode("utf-8")
                            before_s += piece
                            if len(before_s) > before:
                                before_s = before_s[len(before_s)-before:]
                        if piece == needle[needle_i]:
                            needle_i += 1
                        else:
                            needle_i = 0
                        if needle_i >= len(needle):
                            print(SEPARATOR)
                            print("found at: " + str(byte_i) + "["
                                + str(ins.tell()-piece_size) + "]")
                            if last_opener_i is not None:
                                print("  - a {} file starts at"
                                      " {}".format(last_opener_type,
                                                   last_opener_i))
                            else:
                                split_by_bang_path = mkdir_dated(os.getcwd(), now_s=now_s + "_split_by_shebang", unique=False)

                                # betters = split_by_bad(buf)
                                # for better in betters:
                                    # goods = split_by_starters(better)
                                goods = split_by_starters(buf)
                                this_good_count = 0
                                for good in goods:
                                    dot_ext = ".dump.bin"
                                    t = get_type_at(good)
                                    if t is not None:
                                        dot_ext = "." + t
                                    name = "path[" + str(path_i) + "].result[" + str(this_found_count) + "].chunk[" + str(this_good_count) + "]" + dot_ext
                                    path = os.path.join(split_by_bang_path, name)
                                    with open(path, 'wb') as outs:
                                        outs.write(bytearray(good))
                                    this_good_count += 1
                                    this_good_count_total += 1
                                    print("  * wrote '{}'.".format(split_by_bang_path))
                                # print("  /*****displayable chunks in buffer: ")
                                # for buf_bytes in split_by_bad(buf):
                                    # print(str(buf_bytes))  # This is the only thing that works.
                                    # try:
                                        # print(buf_bytes.decode("utf-8"))
                                    # except UnicodeDecodeError:
                                        # try:
                                            # print(buf_bytes.decode("iso-8859-1"))  # latin-1 doesn't allow u'\x8b' even though https://docs.python.org/3/library/codecs.html#standard-encodings says latin-1 or iso-8859-1 are simplest and uses everything 0-255
                                            # # (`UnicodeEncodeError: 'ascii' codec can't encode character u'\x8b' in position 0: ordinal not in range(128)`)
                                        # except UnicodeDecodeError:
                                            # try:
                                                # print(buf_bytes.decode())
                                            # except UnicodeEncodeError:
                                                # print ("// swapdredge says: UNDISPLAYABLE STRING")
                                    # except UnicodeEncodeError:
                                        # raise RuntimeError("There should not be a UnicodeEncodeError here, because buf (and buf_bytes) must always be bytes objects!")
                                # print("  end displayable chunks in buffer*****/")
                                pass
                            sys.stdout.flush()
                            results.append(ins.tell()-piece_size)
                            after_s = ""
                            needle_i = 0
                            this_found_count += 1
                        byte_i += 1
                        rel_mb_byte_i += 1
                        if rel_mb_byte_i >= 1048576:
                            rel_mb_byte_i -= rel_mb_byte_i
                            processed_mb += 1
                            if end is not None:
                                progress(float(math.floor(byte_i/1024)) / float(math.ceil(end/1024)))
                            else:
                                progress(float(processed_mb) / total_mb_f)
                elif command == "dump":
                    dump_s = ""
                    rel_byte_i = 0
                    rel_total = int(config['length'])
                    rel_total_f = float(rel_total)
                    dump_start = int(config['start'])
                    good_start = int(config['start'])
                    ins.seek(dump_start)
                    any_good = False
                    while True:
                        piece = ins.read(piece_size)
                        if piece == "":
                            break  # EOF
                        good_i = 0
                        if not any_good:
                            # Only count initial consecutive bad ones.
                            bad_index = get_bad_index(piece[good_i])
                            if bad_index is None:
                                any_good = True
                            else:
                                last_bad_index = bad_index
                            while (good_i < piece_size) and (bad_index is not None):
                                good_i += 1
                                good_start += 1
                                if (good_i < piece_size):
                                    bad_index = get_bad_index(piece[good_i])
                                    if bad_index is not None:
                                        last_bad_index = bad_index
                        dump_s += piece
                        if end is not None:
                            progress(float(math.floor(byte_i/1024)) / float(math.ceil(end/1024)))
                        else:
                            progress(float(rel_byte_i) / rel_total_f)
                        rel_byte_i += 1
                        if rel_byte_i >= rel_total:
                            break

            endProgress()
            if command == "find":
                print("locations:")
                print("  len(results): " + str(len(results)))
                print("  results: " + str(results))
            elif command == "dump":
                print("")
                if good_start != dump_start:
                    bad_char_hex = ""
                    bad_char_msg = ""
                    if last_bad_index is not None:
                        bad_char_hex = "0x" + c_to_hex(chr(last_bad_index))
                        bad_char_msg = " ({})".format(bad_chars[last_bad_index])
                    else:
                        bad_char_hex = "unknown"
                    print("# The data may not dump as a string due to {} non-text characters (last was {}{}). Try starting at or after {}.".format(good_start-dump_start, bad_char_hex, bad_char_msg, good_start))
                print("# region dump {}".format(dump_start))
                # print(str(dump_s))
                rel_dump_i = 0
                has_bad = False
                for c in dump_s:
                    bad_index = get_bad_index(c)
                    if bad_index is not None:
                        if bad_chars[bad_index] is not None:
                            print("# Bad character(s) exist(s) in the"
                                  " data (found {} at offset {}"
                                  " relative to the dump), so not all"
                                  " of it may show "
                                  "below.".format(bad_chars[bad_index],
                                                  rel_dump_i))
                            has_bad = True
                            break
                    rel_dump_i += 1
                if has_bad:
                    goods = split_by_bad(dump_s)

                    split_by_bad_path = mkdir_dated(os.getcwd())
                    temp_path = tempfile.mkdtemp()

                    print("# See also {}-#.* files in {}.".format(dump_prefix, temp_path))
                    error("* writing {} {}-#.* file(s) to new directory '{}' due to bad characters between chunks...".format(len(goods), dump_prefix, temp_path))
                    file_i = 0
                    bin_count = 0
                    detected_count = 0
                    for good in goods:
                        _default_dot_ext = ".bin"
                        dot_ext = _default_dot_ext
                        for k, flags in openers.items():
                            for flag in flags:
                                if good.startswith(flag):
                                    dot_ext = "." + k
                        if dot_ext != _default_dot_ext:
                            pass
                        elif good.startswith("#!/bin/false"):
                            dot_ext = ".txt"
                        elif good.startswith("# "):
                            dot_ext = ".md"
                        # name = dump_prefix + '{0:04d}'.format(file_i)
                        name = dump_prefix + "-" + str(file_i) + dot_ext
                        path = os.path.join(temp_path, name)
                        error("  * writing '{}'...".format(name))
                        with open(path, 'wb') as outs:
                            outs.write(bytearray(good))
                        if dot_ext == _default_dot_ext:
                            bin_count += 1
                            img_abbrev = imghdr.what(path)
                            if img_abbrev is not None:
                                dot_ext = "." + img_abbrev + ".bin"
                                new_name = dump_prefix + "-" + str(file_i) + dot_ext
                                new_path = os.path.join(temp_path, name)
                                error("  * renaming to '{}'...".format(new_name))
                                shutil.move(path, new_path)
                        else:
                            detected_count += 1
                            new_path = os.path.join(split_by_bad_path, name)
                            shutil.move(path, new_path)
                        file_i += 1
                    if bin_count > 0:
                        error("* wrote {} file(s) to '{}'".format(bin_count, temp_path))
                        error("  * Recover them manually if desired,"
                              " otherwise delete them.")
                        error("  * Unless any are plain text, they are"
                              " useless, since only plain text headers are"
                              " split properly. In the case of binary files"
                              " or raw filesystem images, see standard"
                              " output instead and delete *.bin files"
                              " from the temporary directory.")
                    else:
                        os.rmdir(temp_path)
                    if detected_count > 0:
                        error("* wrote {} file(s) to '{}'".format(detected_count, split_by_bad_path))
                    else:
                        os.rmdir(split_by_bad_path)


                print(dump_s)
                print("# endregion dump")
    except KeyboardInterrupt:
        endProgress()
        print("User cancelled the operation")
        # print(str(current_path) + ":")
        print("at:")
        if command == "dump":
            byte_i = int(config['start']) + rel_byte_i
            processed_mb = float(rel_byte_i) / 1024.0
        print("  path: " + str(current_path))
        print("  byte: " + str(byte_i))
        print("  processed_mb: " + str(processed_mb))
        print("  total_mb: " + str(total_mb))
    if this_good_count_total < 1:
        os.rmdir(split_by_bang_path)


if __name__ == "__main__":
    main()
