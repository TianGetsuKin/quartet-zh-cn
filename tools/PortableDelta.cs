using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;

namespace QuartetZh {
    // Versioned, compressed COPY/INSERT stream. Installation must separately
    // verify original, delta and final SHA-256 against the package manifest.
    public static class PortableDelta {
        const int Window = 32;
        const int Stride = 4096;
        static readonly byte[] Magic = {81,90,72,68,76,84,48,49}; // QZHDLT01
        static ulong Hash(byte[] data, int pos) {
            ulong h=0;
            unchecked { for(int i=0;i<Window;i++) h=h*257+data[pos+i]; }
            return h;
        }
        static bool EqualWindow(byte[] a,int ap,byte[] b,int bp) {
            for(int i=0;i<Window;i++) if(a[ap+i]!=b[bp+i]) return false;
            return true;
        }
        static void Insert(BinaryWriter writer,byte[] data,int start,int count) {
            if(count==0) return;
            writer.Write((byte)1); writer.Write(count); writer.Write(data,start,count);
        }
        public static void Create(string originalPath,string translatedPath,string deltaPath) {
            if(File.Exists(deltaPath)) throw new IOException("Delta output already exists");
            byte[] original=File.ReadAllBytes(originalPath), translated=File.ReadAllBytes(translatedPath);
            var index=new Dictionary<ulong,List<int>>();
            for(int p=0;p<=original.Length-Window;p+=Stride) {
                ulong h=Hash(original,p); List<int> positions;
                if(!index.TryGetValue(h,out positions)) {positions=new List<int>();index[h]=positions;}
                // Repeated blank runs need only a few anchors. This affects
                // compression ratio, never reconstruction correctness.
                if(positions.Count<8) positions.Add(p);
            }
            ulong factor=1; unchecked {for(int i=1;i<Window;i++)factor*=257;}
            using(var file=new FileStream(deltaPath,FileMode.CreateNew,FileAccess.Write))
            using(var zip=new GZipStream(file,CompressionLevel.Optimal))
            using(var writer=new BinaryWriter(zip)) {
                writer.Write(Magic);writer.Write((long)translated.Length);
                int pos=0,literalStart=0;
                ulong rolling=translated.Length>=Window?Hash(translated,0):0;
                while(pos<=translated.Length-Window) {
                    List<int> positions; int best=-1,bestLength=0;
                    if(index.TryGetValue(rolling,out positions)) {
                        foreach(int p in positions) {
                            if(!EqualWindow(original,p,translated,pos))continue;
                            int limit=Math.Min(original.Length-p,translated.Length-pos),length=Window;
                            while(length<limit && original[p+length]==translated[pos+length])length++;
                            if(length>bestLength){best=p;bestLength=length;}
                        }
                    }
                    if(best>=0) {
                        Insert(writer,translated,literalStart,pos-literalStart);
                        writer.Write((byte)0);writer.Write((long)best);writer.Write(bestLength);
                        pos+=bestLength;literalStart=pos;
                        if(pos<=translated.Length-Window)rolling=Hash(translated,pos);
                    } else {
                        if(pos<translated.Length-Window)unchecked {
                            rolling=(rolling-translated[pos]*factor)*257+translated[pos+Window];
                        }
                        pos++;
                        if(pos-literalStart>=1048576){Insert(writer,translated,literalStart,pos-literalStart);literalStart=pos;}
                    }
                }
                Insert(writer,translated,literalStart,translated.Length-literalStart);
                writer.Write((byte)255);
            }
        }
        static void Transfer(Stream input,Stream output,int length,byte[] buffer) {
            while(length>0) {
                int n=input.Read(buffer,0,Math.Min(length,buffer.Length));
                if(n==0)throw new InvalidDataException("Truncated delta/source");
                output.Write(buffer,0,n);length-=n;
            }
        }
        public static void Apply(string originalPath,string deltaPath,string outputPath,long maximumLength) {
            if(maximumLength<0)throw new ArgumentOutOfRangeException("maximumLength");
            if(File.Exists(outputPath))throw new IOException("Output already exists");
            bool created=false;
            try {
                using(var original=File.OpenRead(originalPath))
                using(var delta=File.OpenRead(deltaPath))
                using(var zip=new GZipStream(delta,CompressionMode.Decompress))
                using(var reader=new BinaryReader(zip)) {
                    byte[] magic=reader.ReadBytes(Magic.Length);
                    if(magic.Length!=Magic.Length)throw new InvalidDataException("Missing delta header");
                    for(int i=0;i<Magic.Length;i++)if(magic[i]!=Magic[i])throw new InvalidDataException("Unknown delta format");
                    long expected=reader.ReadInt64(),written=0;
                    if(expected<0 || expected>maximumLength)throw new InvalidDataException("Invalid output length");
                    using(var output=new FileStream(outputPath,FileMode.CreateNew,FileAccess.Write)) {
                        created=true;byte[] buffer=new byte[1048576];
                        while(true) {
                            byte kind=reader.ReadByte();
                            if(kind==255) {
                                if(written!=expected)throw new InvalidDataException("Output length mismatch");
                                if(zip.ReadByte()!=-1)throw new InvalidDataException("Trailing delta data");
                                break;
                            }
                            if(kind!=0 && kind!=1)throw new InvalidDataException("Invalid operation");
                            long offset=kind==0?reader.ReadInt64():0;
                            int length=reader.ReadInt32();
                            if(length<=0 || length>expected-written)throw new InvalidDataException("Invalid operation length");
                            if(kind==0) {
                                if(offset<0 || offset>original.Length-length)throw new InvalidDataException("Copy outside original");
                                original.Position=offset;Transfer(original,output,length,buffer);
                            } else Transfer(zip,output,length,buffer);
                            written+=length;
                        }
                    }
                }
            } catch {
                // Remove only this method's newly created partial output.
                if(created && File.Exists(outputPath))File.Delete(outputPath);
                throw;
            }
        }
    }
}
