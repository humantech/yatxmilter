# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from twisted.internet import protocol, defer
from twisted.python.constants import ValueConstant, Values
from yatxmilter.defaults import Milter
from struct import *
from time import time


class _MConst(Values):
    LONG_SIZE = ValueConstant(4)
    CMD_POS = ValueConstant(4)
    PKG_BEGIN = ValueConstant(5)
    CHUNK_SIZE = ValueConstant(65535)
    VERSION_MIN = ValueConstant(2)


class MilterRequest(object):
    def __init__(self, number):
        self.deferreds = []
        self.number = number
        self.answered = 0
        self.sent = False
        self._defer = defer.Deferred()

    def setWaitNDeferred(self, number):
        self.number = number

    def addDeferred(self, deff):
        self.deferreds.append(deff)
        deff.addCallback(self._callback)

    def getDefer(self):
        return self._defer

    def _callback(self, ret_code):
        if self.sent:
            return

        self.answered += 1

        if ret_code != Milter.ReturnCodes.CONTINUE:
            self.answered = self.number

        if self.answered == self.number:
            self.sent = True
            self._defer.callback(ret_code)


class _MilterProtocolRcv(object):
    recv_commands = {
                   'CONNECT':     r'C',
                   'HELO':        r'H',
                   'RCPT':        r'R',
                   'DATA':        r'T',
                   'UNKNOW':      r'U',
                   'HEADER':      r'L',
                   'BODY':        r'B',
                   'ABORT':       r'A',
                   'MACRO':       r'D',
                   'BODYEOB':     r'E',
                   'QUIT_NC':     r'K',
                   'MAIL':        r'M',
                   'EOH':         r'N',
                   'OPTNEG':      r'O',
                   'QUIT':        r'Q'
                  }

    def __init__(self, protocol):
        self._protocol = protocol
        self.router = {
                          _MilterProtocolRcv.recv_commands['OPTNEG']:  self.DfCmdOptNeg,
                          _MilterProtocolRcv.recv_commands['MACRO']:   self.DfCmdMacro,
                          _MilterProtocolRcv.recv_commands['BODYEOB']: self.DfCmdBodyEob,
                          _MilterProtocolRcv.recv_commands['BODY']:    self.DfCmdBody,
                          _MilterProtocolRcv.recv_commands['QUIT']:    self.DfCmdQuit,
                          _MilterProtocolRcv.recv_commands['QUIT_NC']: self.DfCmdQuit,
                          _MilterProtocolRcv.recv_commands['HELO']:    self.DfCmdHello,
                          _MilterProtocolRcv.recv_commands['ABORT']:   self.DfCmdAbort,
                          _MilterProtocolRcv.recv_commands['CONNECT']: self.DfCmdConnect,
                          _MilterProtocolRcv.recv_commands['MAIL']:    self.DfCmdMail,
                          _MilterProtocolRcv.recv_commands['RCPT']:    self.DfCmdRcpt,
                          _MilterProtocolRcv.recv_commands['DATA']:    self.DfCmdData,
                          _MilterProtocolRcv.recv_commands['HEADER']:  self.DfCmdHeader,
                          _MilterProtocolRcv.recv_commands['EOH']:     self.DfCmdEoh
                        }

    def _DfCmdStringExplode(self, barr):
        i = 0
        begin = 0
        exploded = []

        while i < len(barr):
            if barr[i] == 0 or i == len(barr)-1:
                exploded.append( str(barr[begin:i]) )
                i += 1
                begin = i
            i += 1

        return exploded

    def tryDecode(self, barr):
        cmd = ''.join( chr(i) for i in [barr[_MConst.CMD_POS.value]] )
        barr[_MConst.CMD_POS.value] = 0

        try:
            l = unpack_from(str('!I'), barr[0:_MConst.CMD_POS.value])
        except:
            return None, None, barr

        if len(barr)-_MConst.LONG_SIZE.value < l[0]:
            return None, None, barr
        else:
            return cmd, barr[ _MConst.PKG_BEGIN.value : _MConst.PKG_BEGIN.value+l[0] ], barr[ _MConst.PKG_BEGIN.value+l[0]-1 : ]

    def processCommands(self, cmd, barr):
        if cmd in self.router:
            (self.router[ cmd ])(barr)
        else:
            self.DfCmdUnknown(cmd, barr)

    #OPTNEG
    def DfCmdOptNeg(self, barr):
        try:
            l = unpack_from(str('!III'), barr[0:_MConst.LONG_SIZE.value*3])
            version = l[0]
            flags1 = l[1]
            flags2 = l[2]
        except:
            print('Fatal on getting version!')
            self._DfCmdOptNeg_reply(Milter.ReturnCodes.REJECT)
            return

        if version < _MConst.VERSION_MIN.value:
            print('Incompatible client')
            self._DfCmdOptNeg_reply(Milter.ReturnCodes.REJECT)
            return

        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            m.server_flags = [flags1, flags2]
            req.addDeferred( m.xxfi_negotiate(flags1, flags2) )

        req.getDefer().addCallback(self._DfCmdOptNeg_reply)

    def _DfCmdOptNeg_reply(self, ret_code):
        if len(ret_code) != 4:
            print('invalid reply given by xxfi_negotiate, you should return a vector with 3 int')
            return

        if ret_code[0] == Milter.ReturnCodes.CONTINUE:
            barr = pack(str('!III'), ret_code[1], ret_code[2], ret_code[3])
            self._protocol.send.sendCommand(_MilterProtocolSend.repl_commands['OPTNEG'], barr)
        else:
            self._protocol.send.sendCommand(_MilterProtocolSend.repl_commands['REJECT'], '')

    #MACRO
    def DfCmdMacro(self, barr):
        self._protocol.macros[ barr[0] ] = self._DfCmdMacro_FindParameters(barr[1:])

    def _DfCmdMacro_FindParameters(self, barr):
        begin_name = 0
        begin_value = -1
        att = 0
        ret = {}

        while att < len(barr):
            if barr[att] == 0 or att == len(barr)-1:
                begin_value = att
                att += 1
                while att < len(barr):
                    if barr[att] == 0 or att == len(barr)-1:
                        ret[  str( barr[begin_name:begin_value] )  ] = str( barr[begin_value+1:att] )
                        break
                    att += 1

                begin_name = att + 1
            att += 1

        return ret

    #BODY
    def DfCmdBody(self, barr):
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_body(str(barr)) )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #BODYEOB
    def DfCmdBodyEob(self, barr):
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_body(str(barr)) )
        req.getDefer().addCallback(self.DfCmdBodyEob_reply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    def DfCmdBodyEob_reply(self, reply_code):
        if reply_code != Milter.ReturnCodes.CONTINUE:
            self._protocol.send.DfCmdDefaultReply(reply_code)
            return
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_eom() )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #QUIT
    def DfCmdQuit(self, barr):
        for m in self._protocol.milters:
            m.xxfi_close()

    #HELLO
    def DfCmdHello(self, barr):
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_helo( str(barr) ) )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #ABORT
    def DfCmdAbort(self, barr):
        for m in self._protocol.milters:
            m.xxfi_abort()

    #CONNECT
    def DfCmdConnect(self, barr):
        i = 1
        name = ''
        protocol = Milter.NetworkTypes.UNKNOWN.value
        while i < len(barr):
            if barr[i] == 0 or i == len(barr)-1:
                name = str(barr[0:i])
                break
            i += 1

        i += 1
        if i >= len(barr):
            return self._protocol.send.DfCmdDefaultErr('')

        protocol = str( unichr(barr[i]) )
        i += 1
        req = MilterRequest(len(self._protocol.milters))

        if protocol == Milter.NetworkTypes.UNKNOWN.value:

            for m in self._protocol.milters:
                req.addDeferred( m.xxfi_connect(protocol, None) )

        elif protocol == Milter.NetworkTypes.UNIX.value:

            ii = i
            address = ''

            while ii < len(barr):
                if barr[ii] == 0 or ii == len(bar)-1:
                    address = str(barr[i:ii])
                    break
                ii += 1

            for m in self._protocol.milters:
                m.protocol_connect_ver = protocol
                m.protocol_connect_addr = [address, name]
                req.addDeferred( m.xxfi_connect(protocol, [address, name]) )

        elif protocol == Milter.NetworkTypes.INET.value \
             or protocol == Milter.NetworkTypes.INET6.value:

            port = unpack_from(str('!H'), barr[i:i+2])
            i += 2

            ii = i
            address = ''
            while ii < len(barr):
                if barr[ii] == 0 or ii == len(barr)-1:
                    address = str(barr[i:ii])
                    break
                ii += 1

            for m in self._protocol.milters:
                m.protocol_connect_ver = protocol
                m.protocol_connect_addr = [port[0], address, name]
                req.addDeferred( m.xxfi_connect(protocol, [port[0], address, name]) )

        else:

            req.getDefer().Callback('') #supress warning
            return self._protocol.send.DfCmdDefaultErr('')

        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
#        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #MAIL
    def DfCmdMail(self, barr):
        senders = self._DfCmdStringExplode(barr)
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            m.senders = senders
            req.addDeferred( m.xxfi_env_from(senders) )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #RCPT
    def DfCmdRcpt(self, barr):
        recv = self._DfCmdStringExplode(barr)
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            m.recvs = recv
            req.addDeferred( m.xxfi_env_rcpt(recv) )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #DATA
    def DfCmdData(self, barr):
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_data() )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #HEADER
    def DfCmdHeader(self, barr):
        info = self._DfCmdStringExplode(barr)
        if len(info)<1:
            self._protocol.send.DfCmdDefaultErr('')
            return

        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            if len(info) == 1:
                req.addDeferred( m.xxfi_header(info[0], '') )
            else:
                req.addDeferred( m.xxfi_header(info[0], info[1]) )

        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #EOH
    def DfCmdEoh(self, barr):
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_eoh() )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

    #UNKNOWN
    def DfCmdUnknown(self, cmd, barr):
        req = MilterRequest(len(self._protocol.milters))
        for m in self._protocol.milters:
            req.addDeferred( m.xxfi_unknown(cmd, barr) )
        req.getDefer().addCallback(self._protocol.send.DfCmdDefaultReply)
        req.getDefer().addErrback(self._protocol.send.DfCmdDefaultErr)

class _MilterProtocolSend(object):
    repl_commands = {
                   'ADDRCPT':      r'+',
                   'DELRCPT':      r'-',
                   'ADDRCPT_PAR':  r'2',
                   'SHUTDOWN':     r'4',
                   'ACCEPT':       r'a',
                   'REPLBODY':     r'b',
                   'CONTINUE':     r'c',
                   'DISCARD':      r'd',
                   'CHGFROM':      r'e',
                   'CONN_FAIL':    r'f',
                   'ADDHEADER':    r'h',
                   'INSHEADER':    r'i',
                   'SETSYMLIST':   r'l',
                   'CHGHEADER':    r'm',
                   'PROGRESS':     r'p',
                   'QUARANTINE':   r'q',
                   'REJECT':       r'r',
                   'SKIP':         r's',
                   'TEMPFAIL':     r't',
                   'REPLYCODE':    r'y',
                   'OPTNEG':       r'O'
                  }

    def __init__(self, protocol):
        self._protocol = protocol
        self.repl_relation = {
                              Milter.ReturnCodes.CONTINUE: _MilterProtocolSend.repl_commands['CONTINUE'],
                              Milter.ReturnCodes.REJECT:   _MilterProtocolSend.repl_commands['REJECT'],
                              Milter.ReturnCodes.DISCARD:  _MilterProtocolSend.repl_commands['DISCARD'],
                              Milter.ReturnCodes.ACCEPT:   _MilterProtocolSend.repl_commands['ACCEPT'],
                              Milter.ReturnCodes.TEMPFAIL: _MilterProtocolSend.repl_commands['TEMPFAIL'],
                              Milter.ReturnCodes.SKIP:     _MilterProtocolSend.repl_commands['SKIP']
                             }

    def sendCommand(self, cmd, data):
        ascii_command = cmd.encode('ascii', 'ignore')
        datalen = len(data) + 1
        if datalen > 1:
            encoded = pack(str('!Ic'), datalen, ascii_command) + bytearray(data)
            self._protocol.transport.write( str(encoded) )
        else:
            self._protocol.transport.write( pack(str('!Ic'), datalen, ascii_command) )

    def DfCmdDefaultReply(self, ret_code):
        if ret_code in self.repl_relation:
            self.sendCommand( self.repl_relation[ret_code], '' )
        elif ret_code != Milter.ReturnCodes.NOREPLY:
            self.sendCommand( _MilterProtocolSend.repl_commands['REJECT'], '' )

    def DfCmdDefaultErr(self, fail):
        print(str(fail))
        self.sendCommand( _MilterProtocolSend.repl_commands['TEMPFAIL'], '' )

    def smfiQuarantine(self, reason):
        self.sendCommand(_MilterProtocolSend.repl_commands['QUARANTINE'], bytearray(reason)+bytearray('\0') )

    def smfiReplaceBody(self, body):
        barr = bytearray(body)
        i=0
        while True:
            if len(barr)-i > _MConst.CHUNK_SIZE.value:
                self.sendCommand(_MilterProtocolSend.repl_commands['REPLBODY'], bytearray(barr[i:i+_MConst.CHUNK_SIZE.value])+bytearray('\0') )
            else:
                self.sendCommand(_MilterProtocolSend.repl_commands['REPLBODY'], bytearray(barr[i:])+bytearray('\0') )
                break
            i += _MConst.CHUNK_SIZE.value

    def smfiProgress(self, body):
        self.sendCommand(_MilterProtocolSend.repl_commands['PROGRESS'], '' )

    def smfiDelRcpt(self, args):
        self.sendCommand(_MilterProtocolSend.repl_commands['DELRCPT'], bytearray(args)+bytearray('\0') )

    def smfiAddRcpt(self, rcpt, args):
        if len(args) > 0:
            self.sendCommand(_MilterProtocolSend.repl_commands['ADDRCPT_PAR'], bytearray(rcpt)+bytearray('\0')+bytearray(args)+bytearray('\0') )
        else:
            self.sendCommand(_MilterProtocolSend.repl_commands['ADDRCPT'], bytearray(rcpt)+bytearray('\0') )

    def smfiChgFrom(self, mail, args):
        self.sendCommand( _MilterProtocolSend.repl_commands['CHGFROM'], bytearray(mail)+bytearray('\0')+bytearray(args)+bytearray('\0') )

    def smfiInsHeader(self, index, name, value):
        if index == -1:
            self.sendCommand( _MilterProtocolSend.repl_commands['ADDHEADER'], bytearray(name)+bytearray('\0')+bytearray(value)+bytearray('\0') )
        else:
            self.sendCommand( _MilterProtocolSend.repl_commands['INSHEADER'], pack(str('!I'), index)+bytearray('name')+bytearray('\0')+bytearray(value)+bytearray('\0') )

    def smfiChgHeader(self, name, index, new_h_name):
         self.sendCommand( _MilterProtocolSend.repl_commands['CHGHEADER'], pack(str('!I'), index)+bytearray('name')+bytearray('\0')+bytearray(value)+bytearray('\0') )

    def smfiAddHeader(self, name, value):
         self.sendCommand( _MilterProtocolSend.repl_commands['ADDHEADER'], pack(str('!I'), index)+bytearray('name')+bytearray('\0')+bytearray(value)+bytearray('\0') )

class MilterProtocol(protocol.Protocol):
    def __init__(self):
        self.milters = []
        self.tick_timeout = 0.1

        self._buffer = bytearray()
        self._last_tick = time()
        self.macros = {}

        self.recv = _MilterProtocolRcv(self)
        self.send = _MilterProtocolSend(self)

    #handle the connection
    def connectionMade(self):
        # here it will be cool to add support to other protocols, like unix pipe and so on
        req = MilterRequest(len(self.milters))

        for m in self.milters:
            req.addDeferred( m.xxfi_mta_connect(self.transport.getHost()) )

        req.getDefer().addCallback(self._connectionMade_reply)

    def _connectionMade_reply(self, status):
        if status != Milter.ReturnCodes.CONTINUE and \
           status != Milter.ReturnCodes.ACCEPT:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        for m in self.milters:
            m.xxfi_mta_close()

    #add milter frontend
    def addMilter(self, milter):
        milter.macros = self.macros
        self.milters.append(milter)

    #default data input gateway
    def dataReceived(self, data):
        if (self.tick_timeout + self._last_tick) < time():
            self._buffer = bytearray() #clears buffer on timeout

        self._last_tick = time()
        self._buffer += bytearray(data)

        while len(self._buffer) > 0:
            cmd, barr, self._buffer = self.recv.tryDecode(self._buffer)
            if cmd != '' and cmd != None:
                self.recv.processCommands(cmd, barr)
            else:
                break

class MilterProtocolFactory(protocol.Factory):
    def __init__(self, milters_f):
        self.milters_f=[]
        self.addMilterFactory(milters_f)

    def addMilterFactory(self, milter_f):
        if hasattr(milter_f, '__iter__'):
            self.milters_f += milter_f
        else:
            self.milters_f.append(milter_f)

    def buildProtocol(self, addr):
        m = MilterProtocol()
        for milt in self.milters_f:
            m.addMilter(milt.build_milter(m))
        return m


