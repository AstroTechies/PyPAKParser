# pylint: disable=unused-variable
#import struct
import zlib


class PakParser():
    CompressionMethod = {0: "NONE", 1: "ZLIB",
                         2: "BIAS_MEMORY", 3: "BIAS_SPEED"}

    def __init__(self, filepath):
        self.reader = PakParser.PakReader(filepath)
        self.headers = {}
        self.seekStop = 0
        self.countStop = None
        self.fileVersion = None
        self.recordCount = None

    def List(self, recordName=None):
        if self.seekStop == 0:
            # First we head straight to the footer
            self.reader.fileObj.seek(-44, 2)
            rtn = self.reader.readInt(32, True)
            assert hex(rtn) == "0x5a6f12e1"

            self.fileVersion = self.reader.readInt(32, True)
            indexOffset = self.reader.readInt(64, True)
            indexSize = self.reader.readInt(64, True)

            self.reader.fileObj.seek(indexOffset, 0)
            strLen = self.reader.readInt(32, True)
            mountPoint = self.reader.readLen(strLen, True)
            self.recordCount = self.reader.readInt(32, True)

        else:
            self.reader.fileObj.seek(self.seekStop, 0)
        if recordName not in self.headers.keys():
            for i in range(self.recordCount or self.countStop):
                rec = PakParser.Record()
                rec.Read(self.reader, self.fileVersion, True, True)
                self.headers[rec.fileName] = rec.offset
                if recordName == rec.fileName:
                    self.seekStop = self.reader.fileObj.tell()
                    self.countStop = i
                    break

        return self.headers.keys()

    def Unpack(self, recordName, decode=False):
        if recordName not in self.headers:
            self.List(recordName)
        offset = self.headers[recordName]
        self.reader.fileObj.seek(offset, 0)

        # I don't know why there's a second record but there is, so we read it out
        rec2 = PakParser.Record()
        rec2.Read(self.reader, self.fileVersion, False)
        if PakParser.CompressionMethod[rec2.compressionMethod] == "NONE":
            rec2.Data = self.reader.readLen(rec2.fileSize, False)
            if decode:
                rec2.Data = rec2.Data.decode('iso-8859-1')

        elif PakParser.CompressionMethod[rec2.compressionMethod] == "ZLIB":
            data_decompressed = []
            for block in rec2.compressionBlocks:
                blockOffset = block.Start
                blockSize = block.Size
                self.reader.fileObj.seek(blockOffset, 0)
                memstream = self.reader.readLen(blockSize)
                data_decompressed.append(
                    zlib.decompress(memstream))

            rec2.Data = b''.join(
                data_decompressed)
            if decode:
                rec2.Data = rec2.Data.decode('iso-8859-1')
        else:
            raise NotImplementedError(
                "Unimplemented compression method " + PakParser.CompressionMethod[rec2.compressionMethod])
        rec2.fileName = recordName
        return rec2

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

        def Read(self, reader, fileVersion, includesHeader, quickread=False):

            if includesHeader:
                strLen = reader.readInt(32, True)
                self.fileName = reader.readLen(strLen, True)

            self.offset = reader.readInt(64, True)

            if quickread:
                reader.fileObj.seek(16, 1)
            else:
                self.fileSize = reader.readInt(64, True)
                self.sizeDecompressed = reader.readInt(64, True)

            self.compressionMethod = reader.readInt(32, True)

            if fileVersion <= 1:
                timestamp = reader.readInt(64, True)

            if quickread:
                reader.fileObj.seek(20, 1)
            else:
                sha1hash = reader.readLen(20, True)

            if fileVersion >= 3:
                if self.compressionMethod != 0:
                    blockCount = reader.readInt(32, True)
                    if quickread:
                        reader.fileObj.seek(blockCount * 16, 1)
                    else:
                        for _ in range(blockCount):
                            startOffset = reader.readInt(64, True)
                            endOffset = reader.readInt(64, True)
                            self.compressionBlocks.append(PakParser.Block(
                                startOffset, endOffset - startOffset))
                if quickread:
                    reader.fileObj.seek(5, 1)
                else:
                    isEncrypted = reader.readInt(8, True)
                    self.isEncrypted = isEncrypted > 0
                    compressionBlockSize = reader.readInt(32, True)

    class PakReader():
        def __init__(self, fileObj):
            self.fileObj = fileObj

        def readInt(self, size, unsigned=False):
            '''
            if size == 8:
                bType = b'<B' if unsigned else b'<b'
            if size == 16:
                bType = b'<H'if unsigned else b'<h'
            if size == 32:
                bType = b'<I'if unsigned else b'<i'
            if size == 64:
                bType = b'<Q' if unsigned else b'<q'
            '''

            t = self.fileObj.read(size // 8)
            rtnData = int.from_bytes(t, "little", signed=(not unsigned))
            # rtnData = struct.unpack(bType, t)[0]
            return rtnData

        def readLen(self, length: int, strRtn=False):
            if isinstance(length, bytes):
                length = int.from_bytes(length, 'little')

            rtnData = self.fileObj.read(length)
            if strRtn:
                rtnData = rtnData.strip(b"\x00").decode('iso-8859-1')
            return rtnData
