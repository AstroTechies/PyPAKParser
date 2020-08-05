# pylint: disable=unused-variable
import struct
import zlib


class PakParser():
    CompressionMethod = {0: "NONE", 1: "ZLIB",
                         2: "BIAS_MEMORY", 3: "BIAS_SPEED"}

    def __init__(self, filepath):
        with open(filepath, "rb") as f:
            self.reader = PakParser.PakReader(f)
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
        def __init__(self, fileObj):
            self.fileObj = fileObj

        def Read(self):
            records = []
            # First we head straight to the footer
            self.fileObj.seek(-44, 2)
            rtn = self.readInt(32, True)
            assert hex(rtn) == "0x5a6f12e1"

            fileVersion = self.readInt(32, True)
            indexOffset = self.readInt(64, True)
            indexSize = self.readInt(64, True)

            self.fileObj.seek(indexOffset, 0)
            strLen = self.readInt(32, True)
            mountPoint = self.readLen(strLen, True)
            recordCount = self.readInt(32, True)

            for _ in range(recordCount):
                rec = PakParser.Record()
                rec.Read(self, fileVersion, True)
                r1Pos = self.fileObj.tell()
                self.fileObj.seek(rec.offset, 0)

                # I don't know why there's a second record but there is, so we read it out
                rec2 = PakParser.Record()
                rec2.Read(self, fileVersion, False)

                if PakParser.CompressionMethod[rec.compressionMethod] == "NONE":
                    rec2.Data = self.readLen(rec2.fileSize, True)

                elif PakParser.CompressionMethod[rec.compressionMethod] == "ZLIB":
                    data_decompressed = []
                    for block in rec2.compressionBlocks:
                        blockOffset = block.Start
                        blockSize = block.Size
                        self.fileObj.seek(blockOffset, 0)
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
                self.fileObj.seek(r1Pos, 0)
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

            t = self.fileObj.read(int(size / 8))
            rtnData = int(struct.unpack(
                bType, t)[0])
            return rtnData

        def readLen(self, length, strRtn=False):
            if isinstance(length, bytes):
                length = int.from_bytes(length, 'little')

            rtnData = self.fileObj.read(int(length))
            if strRtn:
                rtnData = rtnData.strip(b"\x00").decode('iso-8859-1')
            return rtnData
