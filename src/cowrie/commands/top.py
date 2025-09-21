# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import annotations
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from cowrie.shell.command import HoneyPotCommand
from cowrie.core.config import CowrieConfig

from openai import OpenAI
import re

commands = {}


class Command_top(HoneyPotCommand):
    BLACK_ON_WHITE='\033[30;47m'
    RESET='\033[0m'
    PROCESS_HEADING="PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND"
    index = 0
    lc = None
    nlines = 0
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
                    reversed_stats = ''.join(reversed(output_pieces[0]))
                    stats_and_white_space_trail = re.split(r"\n", reversed_stats, 1)
                    stats_no_white_space = ''.join(reversed(stats_and_white_space_trail[1]))
                    stats_white_space_trail = stats_and_white_space_trail[0]

                    formatted_msg = stats_no_white_space + "\n" + self.BLACK_ON_WHITE + stats_white_space_trail +  self.PROCESS_HEADING + self.RESET + output_pieces[1]
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
        self.protocol.terminal.makeCursorVisible()
        return HoneyPotCommand.handle_CTRL_C(self)

    def display_new_top_output(self):
        self.index += 1
        if self.index >= len(self.responses):
            self.index = 0
        output = self.responses[self.index]
        self.protocol.terminal.displayTopOutput(bytes(output, 'utf-8'), self.nlines)
        self.nlines = output.count("\n")

commands["/bin/top"] = Command_top
commands["top"] = Command_top
