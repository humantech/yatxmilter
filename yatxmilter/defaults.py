# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from twisted.internet import defer
from twisted.python.constants import ValueConstant, Values
from twisted.python.constants import NamedConstant, Names

class Milter(object):
    class ReturnCodes(Names):
        CONTINUE = NamedConstant()
        REJECT = NamedConstant()
        DISCARD = NamedConstant()
        ACCEPT = NamedConstant()
        TEMPFAIL = NamedConstant()
        SKIP = NamedConstant()
        NOREPLY = NamedConstant()

    class NetworkTypes(Values):
        UNKNOWN = ValueConstant(r'U')
        UNIX = ValueConstant(r'L')
        INET = ValueConstant(r'4')
        INET6 = ValueConstant(r'6')

    class NegotiateFlags(Values):
        CONNECT = ValueConstant(0x00000001)
        HELO = ValueConstant(0x00000002)
        MAIL = ValueConstant(0x00000004)
        RCPT = ValueConstant(0x00000008)
        BODY = ValueConstant(0x00000010)
        HDRS = ValueConstant(0x00000020)
        EOH = ValueConstant(0x00000040)
        HDR = ValueConstant(0x00000080)
        UNKNOWN = ValueConstant(0x00000100)
        DATA = ValueConstant(0x00000200)
        SKIP = ValueConstant(0x00000400)
        RCPT_REJ = ValueConstant(0x00000800)
        NR_CONN = ValueConstant(0x00001000)
        NR_HELO = ValueConstant(0x00002000)
        NR_MAIL = ValueConstant(0x00004000)
        NR_RCPT = ValueConstant(0x00008000)
        NR_DATA = ValueConstant(0x00010000)
        NR_UNKN = ValueConstant(0x00020000)
        NR_EOH = ValueConstant(0x00040000)
        NR_BODY = ValueConstant(0x00080000)
        HDR_LEADSPC = ValueConstant(0x00100000)
        MDS_256K = ValueConstant(0x10000000)
        MDS_1M = ValueConstant(0x20000000)

    def __init__(self, factory, protocol):
        self._factory = factory
        self.protocol = protocol
        self.server_flags = [0, 0]
        self.macros = {}
        self.protocol_connect_ver = Milter.NetworkTypes.UNKNOWN.value
        self.protocol_connect_addr = []
        self.senders = []
        self.recevs = []
        self.data = ''
        self.protocol_version = 6

    def milter_name(self):
        return 'defaultTwistedMilter'

    def milterVersion(self):
        return '0.1'

    #this is callend when a client opens connection with us, allowing
    #we create some sort of filtering if we want to
    def xxfi_mta_connect(self, conn_address):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    #this is called during connectinfo command from milter client
    def xxfi_connect(self, addr_type, conn_address):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_helo(self, hostName):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_env_from(self, senders):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_env_rcpt(self, recs):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_data(self):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_unknown(self, comm, arg):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_header(self, headerf, headerv):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_eoh(self):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_body(self, body):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_eom(self):
        deff = defer.Deferred()
        deff.callback(Milter.ReturnCodes.CONTINUE)
        return deff

    def xxfi_abort(self):
        return None

    def xxfi_close(self):
        return None

    def xxfi_mta_close(self):
        return None

    def xxfi_negotiate(self, flags1, flags2):
        deff = defer.Deferred()
        deff.callback([Milter.ReturnCodes.CONTINUE, self.protocol_version, 
          flags1, 
          flags2
        ])
        return deff

class MilterFactory(object):
    def build_milter(self, proto):
        return Milter(self, proto)


