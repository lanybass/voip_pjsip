#coding=utf-8
import sys
from PyQt5.QtWidgets import (QWidget,QVBoxLayout,QMessageBox, QGridLayout,QPushButton, QApplication,QLCDNumber,QDialog)
#pjsua
import os
import threading
import wave
from time import sleep
import pjsua as pj



def log_cb(level, str, len):
    print str,

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
        print "Press 'a' to answer"

        current_call = call
        call_cb = MyCallCallback(current_call)
        current_call.set_callback(call_cb)

        current_call.answer(180)


class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)
    
    def on_state(self):
        global current_call
        global in_call
        print "Call with", self.call.info().remote_uri,
        print "is", self.call.info().state_text,
        print "last code =", self.call.info().last_code, 
        print "(" + self.call.info().last_reason + ")"
        
        if self.call.info().state == pj.CallState.DISCONNECTED:
            current_call = None
            print 'Current call is', current_call
            in_call = False

        # elif self.call.info().state == pj.CallState.CONFIRMED:
        #     #Call is Answered
        #     print "Call Answered"
        #     wfile = wave.open("./message.wav")
        #     time = (1.0 * wfile.getnframes ()) / wfile.getframerate ()
        #     print str(time) + "ms"
        #     wfile.close()
        #     call_slot = self.call.info().conf_slot
        #     self.wav_player_id=pj.Lib.instance().create_player('./message.wav',loop=False)
        #     self.wav_slot=pj.Lib.instance().player_get_slot(self.wav_player_id)
        #     pj.Lib.instance().conf_connect(self.wav_slot, call_slot)
        #     sleep(time)
        #     pj.Lib.instance().player_destroy(self.wav_player_id)
        #     self.call.hangup()
        #     in_call = False

    # Notification when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            pj.Lib.instance().conf_connect(call_slot, 0)
            pj.Lib.instance().conf_connect(0, call_slot)
            print "Media is now active"
        else:
            print "Media is inactive"


# Function to make call
def make_call(uri):
    try:
        print "Making call to", uri
        return acc.make_call(uri, cb=MyCallCallback())
    except pj.Error, e:
        print "Exception: " + str(e)
        return None

def cb_func(pid) :
    print '%s playback is done' % pid
    current_call.hangup()

def registration():
    
    pass


 
class Example(QWidget):
     
    def __init__(self):
        super( Example,self ).__init__()
         
        self.initUI()
        lib = pj.Lib()

        current_call = None

        my_ua_cfg = pj.UAConfig()
        my_ua_cfg.nameserver = ['8.8.8.8', '8.8.4.4']
        my_ua_cfg.user_agent = "hanxiaotian_bupt"
        # http://www.pjsip.org/python/pjsua.htm#MediaConfig
        my_media_cfg = pj.MediaConfig()
        my_media_cfg.enable_ice = True
    
        #
        # Procedure: Initialize > Create Transpot > Start > Handle calls > Shutdown
        #

        # https://trac.pjsip.org/repos/wiki/Python_SIP/Settings#StartupandShutdown
        # Initialize the Library
        lib.init(ua_cfg=my_ua_cfg, media_cfg=my_media_cfg, log_cfg = pj.LogConfig(level=3, callback=log_cb))
    
        # Create One or More Transports
        transport = lib.create_transport(pj.TransportType.TCP, pj.TransportConfig())
        #transport = lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(0))
        #transport = lib.create_transport(pj.TransportType.TLS, pj.TransportConfig(port=5060)) # SSL
        lib.set_null_snd_dev()

        # Starting the Library
        lib.start()
        lib.handle_events()

        #
        # Registration
        #
        acc_cfg = pj.AccountConfig()
        succeed = 0
        while (succeed == 0):
            print "---------------------------------------------------------------------"
            acc_cfg.id = "sip:101@10.103.241.142"
            # 
            acc_cfg.reg_uri  = "sip:10.103.241.142;transport=tcp"
            #
            acc_cfg.proxy = [] 
       
            server = "10.103.241.142"
            acc_cfg.proxy = [ "sip:10.103.241.142;transport=tcp;lr" ]
            #
            realm = "han"
            #
            username = "101"
            #
            passwd = "101"
            print "---------------------------------------------------------------------"
    
            acc_cfg.auth_cred = [pj.AuthCred(realm, username ,passwd)]
            
            self.acc_cb = MyAccountCallback()
            self.acc = lib.create_account(acc_cfg, cb=self.acc_cb)
            self.acc_cb.wait()
    
            # Conditions are not correct, because when "IP address change detected for account", all other accounts is Forbidden
            if ((str(self.acc.info().reg_status) == "200") or (str(self.acc.info().reg_status) == "403")):
                succeed = 1
            else:
                print ""
                print "Registration failed, status=", self.acc.info().reg_status, \
                  "(" + self.acc.info().reg_reason + ")"
                print ""
                print "Please try again !"
         
         
    def initUI(self):
         
        self.number = QLCDNumber( self ) 
        
        #grid = QVBoxLayout()
        grid = QGridLayout()
        grid.addWidget( self.number,1,0,1,3 )
        

        button_list = []
        names = ['7', '8', '9',
                '4', '5', '6',
                 '1', '2', '3',
                'cls','0', 'call'	]
         
        positions = [(i,j) for i in range(2,6) for j in range(3)]
         
        for position, name in zip(positions, names):
             
            button = QPushButton(name)
            button.clicked.connect(  self.buttonClicked )
            button_list.append( button )
            grid.addWidget(button, *position)
             
        #grid.addLayout( grid_2 )
        self.setLayout( grid )
        #self.set

        self.setGeometry( 600,300,200,300 )
        self.setWindowTitle('Phone')
        self.show()

    def buttonClicked(self):     
        sender = self.sender()
        #self.statusBar().showMessage( sender.text() )
        if len( sender.text() ) < 2:
            print self.number.value()
            self.number.display( self.number.value() * 10 + int( sender.text() ) )
        if sender.text() == "cls":
            self.number.display( 0 )
        if sender.text() == "call":
            server = "10.103.241.142"
            uri = "sip:" + str( int( self.number.value() ) )  + "@" + server
           
            try:
                print "Making call to", uri
                return self.acc.make_call(uri, cb=MyCallCallback())
            except pj.Error, e:
                print "Exception: " + str(e)

            QMessageBox.information(self,                   
                                        u"ti",  
                                        u"calling:" + str( int( self.number.value() ) ),  
                                        QMessageBox.Yes | QMessageBox.No)


       
        print ( sender.text() )         
         
if __name__ == '__main__':
     
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
