#!/usr/bin/env python
# -*- coding: utf-8 -*-

from struct import unpack_from

import ipaddr

NO_IPV4_DB = u"缺少IPv4数据库"


def inet_ntoa(number):
    addresslist = []
    addresslist.append((number >> 24) & 0xff)
    addresslist.append((number >> 16) & 0xff)
    addresslist.append((number >> 8) & 0xff)
    addresslist.append(number & 0xff)
    return ".".join("%d" % i for i in addresslist)


def inet_ntoa6(number):
    addresslist = []
    addresslist.append((number >> 48) & 0xffff)
    addresslist.append((number >> 32) & 0xffff)
    addresslist.append((number >> 16) & 0xffff)
    addresslist.append(number & 0xffff)
    return ":".join("%04X" % i for i in addresslist) + "::"


class IPDBv6(object):
    """ipv6wry.db数据库查询功能集合
    """

    def __init__(self, dbname="ipv6wry.db"):
        """ 初始化类，读取数据库内容为一个字符串
        """

        self.dbname = dbname
        f = open(dbname, "rb")
        self.img = f.read()
        f.close()

        if self.img[:4] != b"IPDB":
            # 数据库格式错误
            return
        if self.getLong8(4, 2) >= 0x100:
            # 数据库格式错误
            return
        self.firstIndex = self.getLong8(16)
        self.indexCount = self.getLong8(8)
        self.offlen = self.getLong8(6, 1)
        self.iplen = self.getLong8(7, 1)

    def getString(self, offset=0):
        """ 读取字符串信息，包括"国家"信息和"地区"信息

        QQWry.Dat的记录区每条信息都是一个以"\0"结尾的字符串"""

        o2 = self.img.find(b"\0", offset)
        # 有可能只有国家信息没有地区信息，
        gb_str = self.img[offset: o2]
        try:
            utf8_str = gb_str.decode()
        except:
            return "未知数据"
        return utf8_str

    def getLong8(self, offset=0, size=8):
        s = self.img[offset: offset + size]
        s += b"\0\0\0\0\0\0\0\0"
        return unpack_from("<Q", s)[0]

    def getAreaAddr(self, offset=0):
        """ 通过给出偏移值，取得区域信息字符串，"""

        byte = self.img[offset]
        if byte == 1 or byte == 2:
            # 第一个字节为1或者2时，取得2-4字节作为一个偏移量调用自己
            p = self.getLong8(offset + 1, self.offlen)
            return self.getAreaAddr(p)
        else:
            return self.getString(offset)

    def getAddr(self, offset, ip=0):
        img = self.img
        o = offset
        byte = img[o]

        if byte == 1:
            # 重定向模式1
            # [IP][0x01][国家和地区信息的绝对偏移地址]
            # 使用接下来的3字节作为偏移量调用字节取得信息
            return self.getAddr(self.getLong8(o + 1, self.offlen))

        else:
            # 重定向模式2 + 正常模式
            # [IP][0x02][信息的绝对偏移][...]
            cArea = self.getAreaAddr(o)
            if byte == 2:
                o += 1 + self.offlen
            else:
                o = self.img.find(b"\0", o) + 1
            aArea = self.getAreaAddr(o)
            return (cArea, aArea)

    def find(self, ip, l, r):
        """ 使用二分法查找网络字节编码的IP地址的索引记录"""
        if r - l <= 1:
            return l

        m = (l + r) // 2
        o = self.firstIndex + m * (8 + self.offlen)
        new_ip = self.getLong8(o)
 
        if ip < new_ip:
            return self.find(ip, l, m)
        else:
            return self.find(ip, m, r)

    def getIPAddr(self, ip, i4obj=None):
        """ 调用其他函数，取得信息！"""
        try:
            # 把IP地址转成数字
            ip6 = int(ipaddr.IPAddress(ip))
        
            ip = (ip6 >> 64) & 0xFFFFFFFFFFFFFFFF
            # 使用 self.find 函数查找ip的索引偏移
            i = self.find(ip, 0, self.indexCount)
            # 得到索引记录
            ip_off = self.firstIndex + i * (8 + self.offlen)
            ip_rec_off = self.getLong8(ip_off + 8, self.offlen)
            (c, a) = self.getAddr(ip_rec_off)
            (cc, aa) = (c, a)
            i1 = inet_ntoa6(self.getLong8(ip_off))
            try:
                i2 = inet_ntoa6(self.getLong8(ip_off + 8 + self.offlen) - 1)
            except:
                i2 = "FFFF:FFFF:FFFF:FFFF::"
            if ip6 == 0x1:  # 本机地址
                i1 = "0:0:0:0:0:0:0:1"
                i2 = "0:0:0:0:0:0:0:1"
                c = cc = u"本机地址"
            elif ip == 0 and ip6 >> 32 & 0xFFFFFFFF == 0xFFFF:  # IPv4映射地址
                realip = (ip6 & 0xFFFFFFFF)
                realipstr = inet_ntoa(realip)
                try:
                    (_, _, realiploc, cc, aa) = i4obj.getIPAddr(realip)
                except:
                    realiploc = NO_IPV4_DB
                i1 = "0:0:0:0:0:FFFF:0:0"
                i2 = "0:0:0:0:0:FFFF:FFFF:FFFF"
                c = u"IPv4映射地址"
                a = a + u"<br/>对应的IPv4地址为" + realipstr + u"，位置为" + realiploc
            elif ip >> 48 & 0xFFFF == 0x2002:  # 6to4
                realip = (ip & 0x0000FFFFFFFF0000) >> 16
                realipstr = inet_ntoa(realip)
                try:
                    (_, _, realiploc, cc, aa) = i4obj.getIPAddr(realip)
                except:
                    realiploc = NO_IPV4_DB
                a = a + u"<br/>对应的IPv4地址为" + realipstr + u"，位置为" + realiploc
            elif ip >> 32 & 0xFFFFFFFF == 0x20010000:  # teredo
                serverip = (ip & 0xFFFFFFFF)
                serveripstr = inet_ntoa(serverip)
                realip = (~ip6 & 0xFFFFFFFF)
                realipstr = inet_ntoa(realip)
                try:
                    (_, _, serveriploc, cc, aa) = i4obj.getIPAddr(serverip)
                    (_, _, realiploc, _, _) = i4obj.getIPAddr(realip)
                except:
                    serveriploc = NO_IPV4_DB
                    realiploc = NO_IPV4_DB
                a = a + u"<br/>Teredo服务器的IPv4地址为" + serveripstr + u"，位置为" + serveriploc
                a = a + u"<br/>客户端真实的IPv4地址为" + realipstr + u"，位置为" + realiploc
            elif ip6 >> 32 & 0xFFFFFFFF == 0x5EFE:  # isatap
                realip = (ip6 & 0xFFFFFFFF)
                realipstr = inet_ntoa(realip)
                try:
                    (_, _, realiploc, _, _) = i4obj.getIPAddr(realip)
                except:
                    realiploc = NO_IPV4_DB
                a = a + u"<br/>ISATAP地址，对应的IPv4地址为" + realipstr + u"，位置为" + realiploc
        except Exception as e:
            i1 = ""
            i2 = ""
            c = cc = u"错误的IP地址"
            a = aa = ""
        return (i1, i2, c + u" " + a, cc, aa)
