#!/usr/env python
import os
import sys

commands = ['find', 'dump']
command_reqs = {}
command_reqs['dump'] = ['start', 'length']

config = {}
config['preview_show_before'] = 512
config['preview_show_after'] = 512
config_help = {}
config_help['find'] = (
    "what word (or phrase in quotes) to find in the file (required)"
)
config_help['preview_show_before'] = (
    "bytes to show before result upon find (default:"
    + str(config['preview_show_before']) + ")"
)
config_help['preview_show_after'] = (
    "bytes to show before result upon find (default:"
    + str(config['preview_show_after']) + ")"
)


def usage():
    print("")
    print("You must specify a file path and required params.")
    print("Params are normally followed by space (but can be followed"
          " by equal sign instead if value has no spaces nor quotes)"
          " then a value.")
    print("Params:")
    for k, v in config_help.items():
        print("--" + k)
        print("  " + v)
    print("")
    print("Example:")
    print("python " + sys.argv[0] + ' image.dd --find "this phrase"')
    print("")


# progress bar functions by 6502 on
# <https://stackoverflow.com/questions/6169217/\
# replace-console-output-in-python>
def startProgress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-"*40 + "]" + chr(8)*41)
    sys.stdout.flush()
    progress_x = 0


def progress(x):
    global progress_x
    x = int(x * 40 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x


def endProgress():
    sys.stdout.write("#" * (40 - progress_x) + "]\n")
    sys.stdout.flush()

def main():
    paths = []
    name = None
    command = None

    for i in range(1, len(sys.argv)):
        # 0 is self
        arg = sys.argv[i]
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
    print("config: " + str(config))
    print("paths: " + str(paths))
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
                        print(this_command + " requires: " + req)
            else:
                did_params = True
    if did_command != 1:
        print("Nothing done since must specify one command:")
        for this_command in commands:
            print("  --" + this_command)
        print("")
        usage()
        exit(1)
    elif not did_params:
        print("")
        usage()
        exit(1)

    piece_size = 1
    needle_i = 0
    needle = config.get("find")
    results = []
    byte_i = 0
    try:
        byte_i = long(0)
    except NameError:
        pass  # already stored long since same as int in Python 3

    before_s = ""
    before = config['preview_show_before']
    after = config['preview_show_after']
    after_s = None
    processed_mb = 0
    byte_i = 0
    current_path = None
    total_mb = None
    rel_byte_i = None
    dump_s = None
    try:
        for i in range(len(paths)):
            path = paths[i]
            #total = os.path.getsize(path)
            if not os.path.isfile(path):
                print("ERROR: no file named '" + path + "'")
                continue
            current_path = path
            total = os.stat(path).st_size
            total_f = float(total)
            total_mb = int(os.stat(path).st_size / 1024 / 1024)
            total_mb_f = float(total_mb)
            rel_mb_byte_i = 0
            processed_mb = 0
            byte_i = 0
            startProgress(path + " progress")
            with open(path, 'rb') as ins:
                if command == "find":
                    while True:
                        piece = ins.read(piece_size)
                        if piece == "":
                            break  # EOF
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
                            print("found at: " + str(byte_i) + "["
                                + str(ins.tell()-piece_size) + "]")
                            results.append(ins.tell()-piece_size)
                            after_s = ""
                            needle_i = 0
                        byte_i += 1
                        rel_mb_byte_i += 1
                        if rel_mb_byte_i >= 1048576:
                            rel_mb_byte_i -= rel_mb_byte_i
                            processed_mb += 1
                            progress(float(processed_mb) / total_mb_f)
                elif command == "dump":
                    dump_s = ""
                    rel_byte_i = 0
                    rel_total = int(config['length'])
                    rel_total_f = float(rel_total)
                    ins.seek(int(config['start']))
                    while True:
                        piece = ins.read(piece_size)
                        if piece == "":
                            break  # EOF
                        dump_s += piece
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
                print("# region dump")
                print(str(dump_s))
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

if __name__ == "__main__":
    main()
