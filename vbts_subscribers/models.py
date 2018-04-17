"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from django.db import models


class DialdataTable(models.Model):
    id = models.IntegerField(primary_key=True)
    exten = models.CharField(max_length=40)
    dial = models.CharField(max_length=128)

    class Meta:
        managed = False
        db_table = 'DIALDATA_TABLE'
        verbose_name = 'Dialdata'
        verbose_name_plural = 'Dialdata'


class Rrlp(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=80)
    latitude = models.FloatField()
    longitude = models.FloatField()
    error = models.FloatField()
    time = models.TextField()

    class Meta:
        managed = False
        db_table = 'RRLP'
        verbose_name = 'RRLP'
        verbose_name_plural = 'RRLP'


class SipBuddies(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=80)
    context = models.CharField(max_length=80, blank=True, null=True)
    callingpres = models.CharField(max_length=30, blank=True, null=True)
    deny = models.CharField(max_length=95, blank=True, null=True)
    permit = models.CharField(max_length=95, blank=True, null=True)
    secret = models.CharField(max_length=80, blank=True, null=True)
    md5secret = models.CharField(max_length=80, blank=True, null=True)
    remotesecret = models.CharField(max_length=250, blank=True, null=True)
    transport = models.CharField(max_length=10, blank=True, null=True)
    host = models.CharField(max_length=31)
    nat = models.CharField(max_length=5)
    type = models.CharField(max_length=10)
    accountcode = models.CharField(max_length=20, blank=True, null=True)
    amaflags = models.CharField(max_length=13, blank=True, null=True)
    callgroup = models.CharField(max_length=10, blank=True, null=True)
    callerid = models.CharField(max_length=80, blank=True, null=True)
    defaultip = models.CharField(max_length=40, blank=True, null=True)
    dtmfmode = models.CharField(max_length=7, blank=True, null=True)
    fromuser = models.CharField(max_length=80, blank=True, null=True)
    fromdomain = models.CharField(max_length=80, blank=True, null=True)
    insecure = models.CharField(max_length=4, blank=True, null=True)
    language = models.CharField(max_length=2, blank=True, null=True)
    mailbox = models.CharField(max_length=50, blank=True, null=True)
    pickupgroup = models.CharField(max_length=10, blank=True, null=True)
    qualify = models.CharField(max_length=3, blank=True, null=True)
    regexten = models.CharField(max_length=80, blank=True, null=True)
    rtptimeout = models.CharField(max_length=3, blank=True, null=True)
    rtpholdtimeout = models.CharField(max_length=3, blank=True, null=True)
    setvar = models.CharField(max_length=100, blank=True, null=True)
    disallow = models.CharField(max_length=100, blank=True, null=True)
    allow = models.CharField(max_length=100)
    fullcontact = models.CharField(max_length=80, blank=True, null=True)
    ipaddr = models.CharField(max_length=45, blank=True, null=True)
    # port: This field type is a guess.
    port = models.TextField(blank=True, null=True)
    username = models.CharField(max_length=80, blank=True, null=True)
    defaultuser = models.CharField(max_length=80, blank=True, null=True)
    subscribecontext = models.CharField(max_length=80, blank=True, null=True)
    directmedia = models.CharField(max_length=3, blank=True, null=True)
    trustrpid = models.CharField(max_length=3, blank=True, null=True)
    sendrpid = models.CharField(max_length=3, blank=True, null=True)
    progressinband = models.CharField(max_length=5, blank=True, null=True)
    promiscredir = models.CharField(max_length=3, blank=True, null=True)
    useclientcode = models.CharField(max_length=3, blank=True, null=True)
    callcounter = models.CharField(max_length=3, blank=True, null=True)
    # busylevel: This field type is a guess.
    busylevel = models.TextField(blank=True, null=True)
    allowoverlap = models.CharField(max_length=3, blank=True, null=True)
    allowsubscribe = models.CharField(max_length=3, blank=True, null=True)
    allowtransfer = models.CharField(max_length=3, blank=True, null=True)
    ignoresdpversion = models.CharField(max_length=3, blank=True, null=True)
    template = models.CharField(max_length=100, blank=True, null=True)
    videosupport = models.CharField(max_length=6, blank=True, null=True)
    # maxcallbitrate: This field type is a guess.
    maxcallbitrate = models.TextField(blank=True, null=True)
    rfc2833compensate = models.CharField(max_length=3, blank=True, null=True)
    # session_timers: Field renamed to remove unsuitable characters.
    session_timers = models.CharField(db_column='session-timers',
                                      max_length=10, blank=True, null=True)
    # session_expired: Field renamed to remove unsuitable characters.
    # This field type is a guess.
    session_expires = models.TextField(db_column='session-expires',
                                       blank=True, null=True)
    # session_minse: Field renamed to remove unsuitable characters.
    # This field type is a guess.
    session_minse = models.TextField(db_column='session-minse',
                                     blank=True, null=True)
    # session_refresher: Field renamed to remove unsuitable characters.
    session_refresher = models.CharField(db_column='session-refresher',
                                         max_length=3, blank=True, null=True)
    t38pt_usertpsource = models.CharField(max_length=3, blank=True, null=True)
    outboundproxy = models.CharField(max_length=250, blank=True, null=True)
    callbackextension = models.CharField(max_length=250, blank=True, null=True)
    registertrying = models.CharField(max_length=3, blank=True, null=True)
    # timert1: This field type is a guess.
    timert1 = models.TextField(blank=True, null=True)
    # timerb: This field type is a guess.
    timerb = models.TextField(blank=True, null=True)
    # qualifyfreq: This field type is a guess.
    qualifyfreq = models.TextField(blank=True, null=True)
    contactpermit = models.CharField(max_length=250, blank=True, null=True)
    contactdeny = models.CharField(max_length=250, blank=True, null=True)
    lastms = models.TextField()  # This field type is a guess.
    regserver = models.CharField(max_length=100, blank=True, null=True)
    regseconds = models.TextField()  # This field type is a guess.
    useragent = models.CharField(max_length=100, blank=True, null=True)
    cancallforward = models.CharField(max_length=3)
    canreinvite = models.CharField(max_length=3)
    mask = models.CharField(max_length=95, blank=True, null=True)
    musiconhold = models.CharField(max_length=100, blank=True, null=True)
    restrictcid = models.CharField(max_length=3, blank=True, null=True)
    # calllimit: This field type is a guess.
    calllimit = models.TextField(blank=True, null=True)
    # whitelistflag: # Field name made lowercase. This field type is a guess.
    whitelistflag = models.TextField(db_column='WhiteListFlag')
    # whitelistcode: Field name made lowercase.
    whitelistcode = models.CharField(db_column='WhiteListCode', max_length=8)
    rand = models.CharField(max_length=33, blank=True, null=True)
    sres = models.CharField(max_length=33, blank=True, null=True)
    ki = models.CharField(max_length=33, blank=True, null=True)
    kc = models.CharField(max_length=33, blank=True, null=True)
    # prepaid: # This field type is a guess.
    prepaid = models.TextField()
    # account_balance: This field type is a guess.
    account_balance = models.TextField()
    # rrlpsupported: Field name made lowercase. This field type is a guess.
    rrlpsupported = models.TextField(db_column='RRLPSupported')
    hardware = models.CharField(max_length=20, blank=True, null=True)
    # regtime: Field name made lowercase.
    regtime = models.IntegerField(db_column='regTime')
    a3_a8 = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'SIP_BUDDIES'
        verbose_name = 'Sip Buddy'
        verbose_name_plural = 'Sip Buddies'

    def __unicode__(self):
        return self.name


class Rates(models.Model):
    rowid = models.IntegerField(primary_key=True)
    service = models.CharField(max_length=30)
    rate = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'rates'
        verbose_name = 'Rate'
        verbose_name_plural = 'Rates'
