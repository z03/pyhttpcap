#coding=utf-8

from __future__ import unicode_literals, print_function, division
__author__ = 'dongliu'

# read and parse pcap file
# see http://wiki.wireshark.org/Development/LibpcapFileFormat
import sys
import struct


class PcapFile(object):
    def __init__(self, infile):
        self.infile = infile
        self.byteorder = b'@'
        self.link_type = None

    # http://www.winpcap.org/ntar/draft/PCAP-DumpFileFormat.html
    def pcap_check(self):
        """check the header of cap file, see it is a ledge pcap file.."""

        # default, auto
        # read 24 bytes header
        pcap_file_header_len = 24
        global_head = self.infile.read(pcap_file_header_len)
        if not global_head:
            raise StopIteration()

        magic_num, = struct.unpack(b'<I', global_head[0:4])
        # judge the endian of file.
        if magic_num == 0xA1B2C3D4:
            self.byteorder = b'<'
        elif magic_num == 0x4D3C2B1A:
            self.byteorder = b'>'
        else:
            return False

        version_major, version_minor, timezone, timestamp, max_package_len, self.link_type \
            = struct.unpack(self.byteorder + b'4xHHIIII', global_head)

        return True

    def read_pcap_pac(self):
        """
        read pcap header.
        return the total package length.
        """
        # package header
        pcap_header_len = 16
        package_header = self.infile.read(pcap_header_len)

        # end of file.
        if not package_header:
            return None, None

        seconds, suseconds, packet_len, raw_len = struct.unpack(self.byteorder + b'IIII', package_header)
        # note: packet_len contains padding.
        link_packet = self.infile.read(packet_len)
        if len(link_packet) < packet_len:
            return None, None
        return packet_len, link_packet

    def read_packet(self):
        flag = self.pcap_check()
        if not flag:
            # not a valid pcap file or we cannot handle this file.
            print("Can't recognize this PCAP file format.", file=sys.stderr)
            return
        while True:
            packet_len, link_packet = self.read_pcap_pac()
            if link_packet:
                yield self.byteorder, self.link_type, link_packet
            else:
                return