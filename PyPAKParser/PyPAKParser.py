# pylint: disable=unused-variable
import struct
import zlib
'''
    Parses both compressed and uncompressed PAK files to look for `metadata.json`

    USAGE:

        from PyPAKParser import PakParser

        PP = PakParser("000-GoodSample_P.pak")
        print(PP.data)

        PP = PakParser("000-CompressedSample_P.pak")
        print(PP.data)

'''


class PakParser():
    CompressionMethod = {0: "NONE", 1: "ZLIB",
                         2: "BIAS_MEMORY", 3: "BIAS_SPEED"}

    def __init__(self, filepath):
        self.data = None
        with open(filepath, "rb") as f:
            self.data = f.read()
        self.reader = PakParser.PakReader(self.data)
        self.records = self.reader.Read()

    class Block():
        def __init__(self, start, size):
            self.Start = start
            self.Size = size

    class Record():
        def __init__(self):
            self.fileName = None
            self.offset = None
            self.fileSize = None
            self.sizeDecompressed = None
            self.compressionMethod = None
            self.isEncrypted = None
            self.compressionBlocks = []
            self.Data = None

        def Read(self, reader, fileVersion, includesHeader):

            if includesHeader:
                strLen = reader.readInt(32, True)
                self.fileName = reader.readLen(strLen, True)

            self.offset = reader.readInt(64, True)
            self.fileSize = reader.readInt(64, True)
            self.sizeDecompressed = reader.readInt(64, True)
            self.compressionMethod = reader.readInt(32, True)

            if fileVersion <= 1:
                timestamp = reader.readInt(64, True)

            sha1hash = reader.readLen(20, True)

            if fileVersion >= 3:
                if self.compressionMethod != 0:
                    blockCount = reader.readInt(32, True)
                    for _ in range(blockCount):
                        startOffset = reader.readInt(64, True)
                        endOffset = reader.readInt(64, True)
                        self.compressionBlocks.append(PakParser.Block(
                            startOffset, endOffset - startOffset))

                isEncrypted = reader.readInt(8, True)
                self.isEncrypted = isEncrypted > 0
                compressionBlockSize = reader.readInt(32, True)

    class PakReader():
        def __init__(self, data):
            self.fullData = data
            self.position = 0

        def Read(self):
            records = []
            # First we head straight to the footer
            self.position = len(self.fullData)-44

            rtn = self.readInt(32, True)
            assert hex(rtn) == "0x5a6f12e1"

            fileVersion = self.readInt(32, True)
            indexOffset = self.readInt(64, True)
            indexSize = self.readInt(64, True)

            self.position = indexOffset
            strLen = self.readInt(32, True)
            mountPoint = self.readLen(strLen, True)
            recordCount = self.readInt(32, True)

            for _ in range(recordCount):
                print('here')
                rec = PakParser.Record()
                rec.Read(self, fileVersion, True)
                r1Pos = self.position
                self.position = rec.offset
                print(f"r1 {rec.fileName}")

                # I don't know why there's a second record but there is, so we read it out
                rec2 = PakParser.Record()
                rec2.Read(self, fileVersion, False)

                if PakParser.CompressionMethod[rec.compressionMethod] == "NONE":
                    rec2.Data = self.readLen(rec2.fileSize, True)
                    #print(f"r2 {rec2.Data}")

                elif PakParser.CompressionMethod[rec.compressionMethod] == "ZLIB":
                    data_decompressed = []
                    for block in rec2.compressionBlocks:
                        blockOffset = block.Start
                        blockSize = block.Size
                        self.position = blockOffset
                        memstream = self.readLen(blockSize)
                        data_decompressed.append(
                            zlib.decompress(memstream))

                    rec2.Data = b''.join(
                        data_decompressed).decode('iso-8859-1')
                else:
                    raise NotImplementedError(
                        "Unimplemented compression method " + PakParser.CompressionMethod[rec.compressionMethod])
                rec2.fileName = rec.fileName
                records.append(rec2)
                self.position = r1Pos
            return records

        def readInt(self, size, unsigned=False):
            unsigned = bool(unsigned)
            size = int(size)
            if size == 8:
                bType = b'<B' if unsigned else b'<b'
            if size == 16:
                bType = b'<H'if unsigned else b'<h'
            if size == 32:
                bType = b'<I'if unsigned else b'<i'
            if size == 64:
                bType = b'<Q' if unsigned else b'<q'

            data = self.fullData[self.position:self.position+int(size/8)]
            rtnData = int(struct.unpack(bType, bytes(data))[0])
            self.position += int(size/8)
            return rtnData

        def readLen(self, length, strRtn=False):
            if isinstance(length, bytes):
                length = int.from_bytes(length, 'little')

            rtnData = self.fullData[self.position:self.position+int(length)]
            self.position += int(length)
            if strRtn:
                rtnData = rtnData.strip(b"\x00").decode('iso-8859-1')
            return rtnData
