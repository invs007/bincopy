from __future__ import print_function

import unittest
import bincopy

class BinCopyTest(unittest.TestCase):

    def test_srec(self):
        binfile = bincopy.BinFile()
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        with open('tests/files/in.s19') as fin:
            self.assertEqual(binfile.as_srec(28, 16), fin.read())

        binfile = bincopy.BinFile()
        with open('tests/files/empty_main.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        with open('tests/files/empty_main.bin', 'rb') as fin:
            self.assertEqual(binfile.as_binary(padding=b'\x00'), fin.read())

        # Add and overwrite the data.
        binfile = bincopy.BinFile()
        binfile.add_srec_file('tests/files/empty_main_rearranged.s19')
        binfile.add_srec_file('tests/files/empty_main_rearranged.s19',
                              overwrite=True)
        with open('tests/files/empty_main.bin', 'rb') as fin:
            self.assertEqual(binfile.as_binary(padding=b'\x00'), fin.read())

        with self.assertRaises(bincopy.Error) as cm:
            binfile.add_srec_file('tests/files/bad_crc.s19')
        self.assertEqual(str(cm.exception),
                         "bad crc in record "
                         "'S2144002640000000002000000060000001800000022'")

    def test_bad_srec(self):
        # pack
        with self.assertRaises(bincopy.Error) as cm:
            bincopy.pack_srec('q', 0, 0, '')
        self.assertEqual(str(cm.exception), "bad type 'q'")

        # unpack too short record
        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_srec('')
        self.assertEqual(str(cm.exception), "bad record ''")

        # unpack bad first character
        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_srec('T0000011')
        self.assertEqual(str(cm.exception), "bad record 'T0000011'")

        # unpack bad type
        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_srec('S.000011')
        self.assertEqual(str(cm.exception), "bad record type '.'")

        # unpack bad crc
        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_srec('S1000011')
        self.assertEqual(str(cm.exception), "bad crc in record 'S1000011'")

    def test_bad_ihex(self):
        # unpack
        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_ihex('')
        self.assertEqual(str(cm.exception), "bad record ''")

        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_ihex('.0011110022')
        self.assertEqual(str(cm.exception), "bad record '.0011110022'")

        with self.assertRaises(bincopy.Error) as cm:
            bincopy.unpack_ihex(':0011110022')
        self.assertEqual(str(cm.exception), "bad crc in record ':0011110022'")

    def test_ihex(self):
        binfile = bincopy.BinFile()
        with open('tests/files/in.hex', 'r') as fin:
            binfile.add_ihex(fin.read())
        with open('tests/files/in.hex') as fin:
            self.assertEqual(binfile.as_ihex(), fin.read())

        # Add and overwrite the data.
        binfile = bincopy.BinFile()
        binfile.add_ihex_file('tests/files/in.hex')
        binfile.add_ihex_file('tests/files/in.hex', overwrite=True)
        with open('tests/files/in.hex') as fin:
            self.assertEqual(binfile.as_ihex(), fin.read())

    def test_binary(self):
        # Add data to 0..2.
        binfile = bincopy.BinFile()
        with open('tests/files/binary1.bin', 'rb') as fin:
            binfile.add_binary(fin.read())
        with open('tests/files/binary1.bin', 'rb') as fin:
            self.assertEqual(binfile.as_binary(), fin.read())

        # Add and overwrite data to 15..179.
        binfile = bincopy.BinFile()
        binfile.add_binary_file('tests/files/binary2.bin', 15)
        binfile.add_binary_file('tests/files/binary2.bin', 15, overwrite=True)
        with self.assertRaises(bincopy.Error) as cm:
            # cannot add overlapping segments
            with open('tests/files/binary2.bin', 'rb') as fin:
                binfile.add_binary(fin.read(), 20)

        # Exclude the overlapping part and add.
        binfile.exclude(20, 1024)
        with open('tests/files/binary2.bin', 'rb') as fin:
            binfile.add_binary(fin.read(), 20)
        with open('tests/files/binary3.bin', 'rb') as fin:
            self.assertEqual(binfile.as_binary(minimum_address=0,
                                               padding=b'\x00'), fin.read())

        # Exclude first byte ad readd it to test adjecent add before.
        binfile.exclude(0, 1)
        binfile.add_binary(b'1')
        with open('tests/files/binary3.bin', 'rb') as fin:
            reference = b'1' + fin.read()[1:]
            self.assertEqual(binfile.as_binary(minimum_address=0,
                                               padding=b'\x00'), reference)

        # Dump with too high start address
        with self.assertRaises(bincopy.Error) as cm:
            binfile.as_binary(minimum_address=512)
        self.assertEqual(str(cm.exception),
                         'the selected start address must be lower or equal '
                         'to the start address of the binary')

    def test_array(self):
        binfile = bincopy.BinFile()
        with open('tests/files/in.hex', 'r') as fin:
            binfile.add_ihex(fin.read())
        with open('tests/files/in.i') as fin:
            self.assertEqual(binfile.as_array() + '\n', fin.read())

    def test_hexdump(self):
        binfile = bincopy.BinFile()
        binfile.add_binary(b'12',address=17)
        binfile.add_binary(b'34', address=26)
        binfile.add_binary(b'5678', address=30)
        binfile.add_binary(b'9', address=47)
        with open('tests/files/hexdump.txt') as fin:
            self.assertEqual(binfile.as_hexdump(), fin.read())

        binfile = bincopy.BinFile()
        binfile.add_binary(b'34', address=0x150)
        binfile.add_binary(b'3', address=0x163)
        binfile.add_binary(b'\x01', address=0x260)
        binfile.add_binary(b'3', address=0x263)
        with open('tests/files/hexdump2.txt') as fin:
            self.assertEqual(binfile.as_hexdump(), fin.read())

    def test_srec_ihex_binary(self):
        binfile = bincopy.BinFile()
        with open('tests/files/in.hex', 'r') as fin:
            binfile.add_ihex(fin.read())
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        with open('tests/files/binary1.bin', 'rb') as fin:
            binfile.add_binary(fin.read(), 1024)
        with open('tests/files/out.hex', 'r') as fin:
            self.assertEqual(binfile.as_ihex(), fin.read())
        with open('tests/files/out.s19') as fin:
            self.assertEqual(binfile.as_srec(address_length_bits=16), fin.read())
        binfile.fill(b'\x00')
        with open('tests/files/out.bin', 'rb') as fin:
            self.assertEqual(binfile.as_binary(), fin.read())

    def test_exclude_crop(self):
        # Exclude part of the data.
        binfile = bincopy.BinFile()
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        binfile.exclude(2, 4)
        with open('tests/files/in_exclude_2_4.s19') as fin:
            self.assertEqual(binfile.as_srec(32, 16), fin.read())

        binfile = bincopy.BinFile()
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        binfile.exclude(3, 1024)
        with open('tests/files/in_exclude_3_1024.s19') as fin:
            self.assertEqual(binfile.as_srec(32, 16), fin.read())

        binfile = bincopy.BinFile()
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        binfile.exclude(0, 9)
        with open('tests/files/in_exclude_0_9.s19') as fin:
            self.assertEqual(binfile.as_srec(32, 16), fin.read())

        binfile = bincopy.BinFile()
        with open('tests/files/empty_main.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        binfile.exclude(0x400240, 0x400600)
        with open('tests/files/empty_main_mod.bin', 'rb') as fin:
            self.assertEqual(binfile.as_binary(padding=b'\x00'), fin.read())

        # Crop part of the data.
        binfile = bincopy.BinFile()
        binfile.add_srec_file('tests/files/in.s19')
        binfile.crop(2, 4)
        with open('tests/files/in_crop_2_4.s19') as fin:
            self.assertEqual(binfile.as_srec(32, 16), fin.read())
        binfile.exclude(2, 4)
        self.assertEqual(binfile.as_binary(), b'')

        # Exclude various parts of segments.
        binfile = bincopy.BinFile()
        binfile.add_binary(b'111111', address=8)
        binfile.add_binary(b'222222', address=16)
        binfile.add_binary(b'333333', address=24)

        binfile.exclude(7, 8)
        binfile.exclude(15, 16)
        binfile.exclude(23, 24)
        self.assertEqual(binfile.as_binary(),
                         b'111111' +
                         2 * b'\xff' +
                         b'222222' +
                         2 * b'\xff' +
                         b'333333')

        binfile.exclude(20, 24)
        self.assertEqual(binfile.as_binary(),
                         b'111111' +
                         2 * b'\xff' +
                         b'2222' +
                         4 * b'\xff' +
                         b'333333')

        binfile.exclude(12, 24)
        self.assertEqual(binfile.as_binary(),
                         b'1111' +
                         12 * b'\xff' +
                         b'333333')

        binfile.exclude(11, 25)
        self.assertEqual(binfile.as_binary(),
                         b'111' +
                         14 * b'\xff' +
                         b'33333')

        binfile.exclude(11, 26)
        self.assertEqual(binfile.as_binary(),
                         b'111' +
                         15 * b'\xff' +
                         b'3333')

        # Exclude negative address range and expty address range.
        binfile = bincopy.BinFile()
        binfile.add_binary(b'111111')
        with self.assertRaises(bincopy.Error) as cm:
            binfile.exclude(4, 2)
        self.assertEqual(str(cm.exception), 'bad address range')
        binfile.exclude(2, 2)
        self.assertEqual(binfile.as_binary(), b'111111')

    def test_minimum_maximum(self):
        binfile = bincopy.BinFile()

        # Get the minimum address from an empty file.
        with self.assertRaises(bincopy.Error) as cm:
            binfile.get_minimum_address()
        self.assertEqual(str(cm.exception),
                         'cannot get minimum address from an empty file')

        # Get the maximum address from an empty file.
        with self.assertRaises(bincopy.Error) as cm:
            binfile.get_maximum_address()
        self.assertEqual(str(cm.exception),
                         'cannot get maximum address from an empty file')

        # Get from a small file.
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        self.assertEqual(binfile.get_minimum_address(), 0)
        self.assertEqual(binfile.get_maximum_address(), 70)

    def test_iter_segments(self):
        binfile = bincopy.BinFile()
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        i = 0
        for begin, end, data in binfile.iter_segments():
            del begin, end, data
            i += 1
        self.assertEqual(i, 1)

    def test_add_files(self):
        binfile = bincopy.BinFile()
        binfile_1_2 = bincopy.BinFile()
        binfile.add_binary(b'\x00')
        binfile_1_2.add_binary(b'\x01', address=1)
        binfile += binfile_1_2
        self.assertEqual(binfile.as_binary(), b'\x00\x01')

    def test_info(self):
        binfile = bincopy.BinFile()
        with open('tests/files/empty_main.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        self.assertEqual(binfile.info(), """header: "bincopy/empty_main.s19"
execution start address: 0x00400400
data:
        0x00400238 - 0x004002b4
        0x004002b8 - 0x0040033e
        0x00400340 - 0x004003c2
        0x004003d0 - 0x00400572
        0x00400574 - 0x0040057d
        0x00400580 - 0x004006ac
        0x00600e10 - 0x00601038
""")

    def test_execution_start_address(self):
        binfile = bincopy.BinFile()
        with open('tests/files/empty_main.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        self.assertEqual(binfile.get_execution_start_address(), 0x00400400)

        binfile.set_execution_start_address(0x00400401)
        self.assertEqual(binfile.get_execution_start_address(), 0x00400401)

    def test_ihex_crc(self):
        self.assertEqual(bincopy.crc_ihex('0300300002337a'), 0x1e)
        self.assertEqual(bincopy.crc_ihex('00000000'), 0)

    def test_word_size(self):
        binfile = bincopy.BinFile(word_size_bits=16)
        with open('tests/files/in_16bits_word.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        with open('tests/files/out_16bits_word.s19') as fin:
            self.assertEqual(binfile.as_srec(30, 24), fin.read())

    def test_print(self):
        binfile = bincopy.BinFile()
        with open('tests/files/in.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        print(binfile)

    def test_issue_4_1(self):
        binfile = bincopy.BinFile()
        with open('tests/files/issue_4_in.hex', 'r') as fin:
            binfile.add_ihex(fin.read())
        with open('tests/files/issue_4_out.hex', 'r') as fin:
            self.assertEqual(binfile.as_ihex(), fin.read())

    def test_issue_4_2(self):
        binfile = bincopy.BinFile()
        with open('tests/files/empty_main.s19', 'r') as fin:
            binfile.add_srec(fin.read())
        with open('tests/files/empty_main.hex', 'r') as fin:
            self.assertEqual(binfile.as_ihex(), fin.read())

    def test_overwrite(self):
        binfile = bincopy.BinFile()

        # overwrite in empty file
        binfile.add_binary(b'1234', address=512, overwrite=True)
        self.assertEqual(binfile.as_binary(minimum_address=512), b'1234')

        # test setting data with multiple existing segments
        binfile.add_binary(b'123456', address=1024)
        binfile.add_binary(b'99', address=1026, overwrite=True)
        self.assertEqual(binfile.as_binary(minimum_address=512),
                         b'1234' + 508 * b'\xff' + b'129956')

        # test setting data crossing the original segment limits
        binfile.add_binary(b'abc', address=1022, overwrite=True)
        binfile.add_binary(b'def', address=1029, overwrite=True)
        self.assertEqual(binfile.as_binary(minimum_address=512),
                                           b'1234'
                                           + 506 * b'\xff'
                                           + b'abc2995def')

        # overwrite a segment and write outside it
        binfile.add_binary(b'111111111111', address=1021, overwrite=True)
        self.assertEqual(binfile.as_binary(minimum_address=512),
                                           b'1234'
                                           + 505 * b'\xff'
                                           + b'111111111111')

        # overwrite multiple segments (all segments in this test)
        binfile.add_binary(1024 * b'1', address=256, overwrite=True)
        self.assertEqual(binfile.as_binary(minimum_address=256), 1024 * b'1')

    def test_fill(self):
        binfile = bincopy.BinFile()

        # fill empty file
        binfile.fill()
        self.assertEqual(binfile.as_binary(), b'')

    def test_performance(self):
        binfile = bincopy.BinFile()

        # Add a 1MB consecutive binary.
        chunk = 1024 * b"1"
        for i in range(1024):
            binfile.add_binary(chunk, 1024 * i)

        self.assertEqual(binfile.get_minimum_address(), 0)
        self.assertEqual(binfile.get_maximum_address(), 1024 * 1024)

        ihex = binfile.as_ihex()
        srec = binfile.as_srec()

        binfile = bincopy.BinFile()
        binfile.add_ihex(ihex)

        binfile = bincopy.BinFile()
        binfile.add_srec(srec)


if __name__ == '__main__':
    unittest.main()
