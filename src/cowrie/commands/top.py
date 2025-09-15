# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import annotations
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from cowrie.shell.command import HoneyPotCommand
from cowrie.core.config import CowrieConfig

from openai import OpenAI

commands = {}


class Command_top(HoneyPotCommand):
    BLACK_ON_WHITE='\033[30;47m'
    RESET='\033[0m'
    PROCESS_HEADING="PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND"
    index = 0
    lc = None
    nlines = 0
    # x = "top - 15:32:45 up 10 days,  4:12,  3 users,  load average: 0.42, 0.55, 0.60\nTasks: 195 total,   1 running, 194 sleeping,   0 stopped,   0 zombie\n%Cpu(s):  5.3 us,  1.0 sy,  0.0 ni, 93.2 id,  0.4 wa,  0.0 hi,  0.1 si,  0.0 st\nKiB Mem :  8163956 total,  1234560 free,  4567892 used,  2361504 buff/cache\nKiB Swap:  2097148 total,  2097148 free,        0 used.  3124572 avail Mem\n  \033[30;47mPID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND\033[0m\n 2345 ROOT      20   0  134432  15432   8760 S   7.3  0.2   0:03.26 chrome\n 1789 ROOT      20   0  265804  12344   9344 S   3.0  0.2   0:01.14 mysqld\n 3120 ROOTT     20   0  101340   8464   6780 R   2.0  0.1   0:00.56 top\n 1422 ROOT      20   0  145312  24512  15300 S   0.7  0.3   0:10.55 code\n 2500 ROOT      20   0  105640  12000   9600 S   0.3  0.1   0:00.08 sshd\n 1001 ROOTT     20   0   85600   7520   6920 S   0.0  0.1   0:01.02 bash\n"
    # y = "top - 25:80:45 up 10 days,  4:12,  3 users,  load average: 0.42, 0.55, 0.60\nTasks: 195 total,   1 running, 194 sleeping,   0 stopped,   0 zombie\n%Cpu(s):  5.3 us,  1.0 sy,  0.0 ni, 93.2 id,  0.4 wa,  0.0 hi,  0.1 si,  0.0 st\nKiB Mem :  8163956 total,  1234560 free,  4567892 used,  2361504 buff/cache\nKiB Swap:  2097148 total,  2097148 free,        0 used.  3124572 avail Mem\n  \033[30;47mPID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND\033[0m\n 2345 KATH      20   0  134432  15432   8760 S   7.3  0.2   0:03.26 chrome\n 1789 KATH      20   0  265804  12344   9344 S   3.0  0.2   0:01.14 mysqld\n 3120 KATHH     20   0  101340   8464   6780 R   2.0  0.1   0:00.56 top\n 1422 KATH      20   0  145312  24512  15300 S   0.7  0.3   0:10.55 code\n 2500 KATH      20   0  105640  12000   9600 S   0.3  0.1   0:00.08 sshd\n 1001 KATHH     20   0   85600   7520   6920 S   0.0  0.1   0:01.02 bash\n"
    # z = "top - 35:95:45 up 10 days,  4:12,  3 users,  load average: 0.42, 0.55, 0.60\nTasks: 195 total,   1 running, 194 sleeping,   0 stopped,   0 zombie\n%Cpu(s):  5.3 us,  1.0 sy,  0.0 ni, 93.2 id,  0.4 wa,  0.0 hi,  0.1 si,  0.0 st\nKiB Mem :  8163956 total,  1234560 free,  4567892 used,  2361504 buff/cache\nKiB Swap:  2097148 total,  2097148 free,        0 used.  3124572 avail Mem\n  \033[30;47mPID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND\033[0m\n 2345 AVAA      20   0  134432  15432   8760 S   7.3  0.2   0:03.26 chrome\n 1789 AVAA      20   0  265804  12344   9344 S   3.0  0.2   0:01.14 mysqld\n 3120 AVAAA     20   0  101340   8464   6780 R   2.0  0.1   0:00.56 top\n 1422 AVAA      20   0  145312  24512  15300 S   0.7  0.3   0:10.55 code\n 2500 AVAA      20   0  105640  12000   9600 S   0.3  0.1   0:00.08 sshd\n 1001 AVAAA     20   0   85600   7520   6920 S   0.0  0.1   0:01.02 bash\n"
    # responses = [x, y, z]
    responses = []

    def retrieve_top_output(self):
        prompt = CowrieConfig.get("honeypot", "open_ai_prompt")
        openai_api_key = CowrieConfig.get("honeypot", "open_ai_api_key")
        client = OpenAI(api_key=openai_api_key)

        raw = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.0
        )

        delim = CowrieConfig.get("honeypot", "open_ai_delim")
        raw_msg = raw.choices[0].message.content.replace("```", "")
        outputs = raw_msg.split(delim)

        for o in outputs:
            if o != "":
                output_pieces = o.split(self.PROCESS_HEADING)

                if len(output_pieces) == 2:
                    formatted_msg = output_pieces[0] + self.BLACK_ON_WHITE + "-    -" +  self.PROCESS_HEADING + self.RESET + output_pieces[1]
                    self.responses.append(formatted_msg)

    def start(self) -> None:
        self.retrieve_top_output()
        reactor.callFromThread(self.begin_displaying_top_output)

    def begin_displaying_top_output(self) -> None:
        self.lc = LoopingCall(self.display_new_top_output)
        self.lc.start(3)

    def handle_CTRL_C(self) -> None:
        if self.lc:
            self.lc.stop()
            self.lc = None
        return HoneyPotCommand.handle_CTRL_C(self)

    def display_new_top_output(self):
        self.index += 1
        if self.index >= len(self.responses):
            self.index = 0
        output = self.responses[self.index]
        self.protocol.terminal.topPlayingAround(bytes(output, 'utf-8'), self.nlines)
        self.nlines = output.count("\n")

commands["/bin/top"] = Command_top
commands["top"] = Command_top
