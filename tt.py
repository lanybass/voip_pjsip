#!/usr/bin/python
#
#
# Copyright (C) 2003-2008 Benny Prijono <benny@prijono.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA 
#
# --------------------------------------------------------------------------
#  Modified by Shoaib Ahmed (AKA Sufi-Al-Hussaini)
# --------------------------------------------------------------------------
#

import sys
import signal
import pjsua as pj
import threading
import subprocess
from time import sleep

LOG_LEVEL = 4

SIP_DOMAIN = "10.103.241.142"
SIP_USRNM = "102"
SIP_PWD = "102"

current_call = None
lib = None
acc = None

# Logging callback
def log_cb(level, str, len):
    print str,


def signal_handler(signal, frame):
    if acc is not None:
        acc.delete()
        acc = None
    if lib is not None:
        lib.destroy()
        lib = None
    sys.exit(0)


# Play call audio on audio device 
def play_call_audio(call):
    sleep(0.5)
    call.answer(200)


# Callback to receive events from account
class MyAccountCallback(pj.AccountCallback):
    sem = None

    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)

    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

    # Notification on incoming call
    def on_incoming_call(self, call):
        global current_call 
        if current_call:
            call.answer(486, "Busy")
            return
            
        print "Incoming call from ", call.info().remote_uri
        current_call = call

        call_cb = MyCallCallback(current_call)
        current_call.set_callback(call_cb)

        try:
            play_call_audio(current_call)
        except pj.Error, e:
            print "Exception: " + str(e)
            return None

        
# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):

    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self):
        global current_call
        print "Call with", self.call.info().remote_uri,
        print "is", self.call.info().state_text,
        print "last code =", self.call.info().last_code, 
        print "(" + self.call.info().last_reason + ")"
        
        if self.call.info().state == pj.CallState.DISCONNECTED:
            current_call = None

    # Notification when call's media state has changed.
    def on_media_state(self):
        try:
            if self.call.info().media_state == pj.MediaState.ACTIVE:
                # Connect the call to sound device
                call_slot = self.call.info().conf_slot
                pj.Lib.instance().conf_connect(call_slot, 0)
                pj.Lib.instance().conf_connect(0, call_slot)
                print "Media is now active"
            else:
                print "Media is inactive"
        except pj.Error, e:
            print "Exception: " + str(e)
            if not current_call:
                print "There is no call"
                return
            current_call.hangup()


# Create library instance
lib = pj.Lib()

try:
    lib.init(log_cfg = pj.LogConfig(level=LOG_LEVEL, callback=log_cb))
    lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(5080))
    lib.start()

    # snd_dev = lib.get_snd_dev()
    # print snd_dev
    # lib.set_snd_dev(0,0)

    acc = lib.create_account(pj.AccountConfig(SIP_DOMAIN, SIP_USRNM, SIP_PWD))

    acc_cb = MyAccountCallback(acc)
    acc.set_callback(acc_cb)
    acc_cb.wait()

    print "\n"
    print "Registration complete, status=", acc.info().reg_status, \
          "(" + acc.info().reg_reason + ")"
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()

    acc.delete()
    acc = None
    lib.destroy()
    lib = None

except pj.Error, e:
    print "Exception: " + str(e)    
    if acc is not None:
        acc.delete()
        acc = None
    if lib is not None:
        lib.destroy()
        lib = None
