"""Encode each room with a local tile dictionary and separate sparse positions."""
from array import array
from collections import Counter
import base64,struct
def var(v,out):
 while v>=128:out.append((v&127)|128);v>>=7
 out.append(v)
def compress_room(encoded):
 data=array('H');data.frombytes(base64.b64decode(encoded));ids=[];gaps=[];lengths=[];n=0;i=0
 while i<len(data):
  gap=data[i];i+=1
  if gap==65535:lengths.append(n);n=0;continue
  ids.append(data[i]);gaps.append(gap);i+=1;n+=1
 keys=[k for k,_ in Counter(ids).most_common()];local={v:i for i,v in enumerate(keys)}
 out=bytearray();var(len(keys),out)
 for k in keys:var(k,out)
 var(len(lengths),out)
 for l in lengths:var(l,out)
 for v in gaps:var(v,out)
 for v in ids:var(local[v],out)
 return bytes(out)
