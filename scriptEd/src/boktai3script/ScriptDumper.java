package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.HashMap;

public class ScriptDumper {
   
   ArrayList lines;
   HashMap charMap;
   ScriptMetadata mData;
   ProtectedZones protectedZones;
   
   public ScriptDumper () {
      lines = new ArrayList();
      charMap = new HashMap(1999);
      mData = new ScriptMetadata();
      protectedZones = new ProtectedZones();
      buildCharMap("chartable.sjs.tbl");
   }
   
   private byte[] toByteArray(Byte[] a) {
      int len = a.length;
      byte[] b = new byte[len];
      for (int i = 0; i < len; i++) {
         b[i] = a[i].byteValue();
      }
      return b;
   }
   public void writeToFile(String fileName) {
      //PrintWriter file = null;
      RandomAccessFile file = null;
      int len = lines.size();
      try {
         //file = new PrintWriter(new BufferedOutputStream(new FileOutputStream(fileName)));
         file = new RandomAccessFile(fileName, "rw");
      } catch (IOException e) {
         System.err.println("Unable to open file for writing: " + e.getMessage());
         System.exit(1);
      }
      ArrayList line;
      int idx = 0;
      ListIterator iter = lines.listIterator();
      while (iter.hasNext()) {
         line = (ArrayList) iter.next();
         String lineCode = "J";
         int lineLen = line.size();
         if (lineLen > 0) {
            if (line.get(lineLen-1) instanceof String) {
               line.remove(lineLen-1);
               lineCode = "X";
            }
         }
         byte[] bytes = toByteArray((Byte[])line.toArray(new Byte[0]));
         try {
            file.writeBytes("$" + lineCode + "=====" + idx + "=====\n");
            file.write(bytes);
            file.writeBytes("\n");
         } catch (IOException e) {
            System.err.println("Unable to write to file: " + e.getMessage());
            System.exit(1);
         }
         idx++;
      }
      try {
         file.close();
      } catch (IOException e) {
      }
   }
   
   int pointerTableLookup(byte[] buf, int i, DataFlag dataFlag) {
      int a = buf[i];
      int b = buf[i+1];
      int c = buf[i+2];
      int d = buf[i+3];
      if (a < 0) a += 256;
      if (b < 0) b += 256;
      if (c < 0) c += 256;
      if (d < 0) d += 256;
      int result = a + (b << 8) + (c << 16);
      if ((d & 0x80) != 0) {
         d &= 0x7F;
         dataFlag.setData(false);
      } else {
         dataFlag.setData(true);
      }
      result += (d << 24);
      return result;
   }
   
   void extractFromFile(String fileName) {
      lines.clear();
      mData = new ScriptMetadata();
      byte[] ptableBuf = new byte[40000];
      byte[] scriptBuf = new byte[401000];
      RandomAccessFile file = null;
      try {
         file = new RandomAccessFile(fileName, "r");
      } catch (IOException e) {
         System.err.println("Unable to open file for reading: " + e.getMessage());
         System.exit(1);
      }
      System.out.println("Prefetching pointer table...");
      try {
         file.seek(0xD6B1F8);
         file.read(ptableBuf);
      } catch (IOException e) {
         System.err.println("Unable to read from file: " + e.getMessage());
      }
      System.out.println("Prefetching script...");
      try {
         file.seek(0xD74DDC);
         file.read(scriptBuf);
      } catch (IOException e) {
         System.err.println("Unable to read from file: " + e.getMessage());
      }
      ArrayList line;
      for (int i = 0; i <= 39904; i += 4) {
         DataFlag dataFlag = new DataFlag(false);
         boolean isData = false;
         int idx = pointerTableLookup(ptableBuf, i, dataFlag);
         isData = dataFlag.isData();
         int nextIdx = (i < 39904) ? pointerTableLookup(ptableBuf, i+4, dataFlag) : -1;
         if (isData) {
            protectedZones.addZone((i/4), idx, nextIdx-1);
         }
         line = new ArrayList();
         ArrayList chr = new ArrayList();
         while (idx < nextIdx-1 || (isData && idx < nextIdx) || (nextIdx == -1 && scriptBuf[idx] != 0)) {
            byte x = scriptBuf[idx];
            byte y = scriptBuf[idx+1];
            chr.clear();
            chr.add(new Byte(x));
            idx++;
            if (x >= -128 && x < -122) {
               chr.add(new Byte(y));
               idx++;
            }
            line.addAll((ArrayList)charMap.get(chr));
         }
         //if (scriptBuf[idx] == 0 || nextIdx == -1) {
         if (isData) {
            line.add(new String("JUNK"));
         }
         lines.add(line);
      }
      System.out.println("Lines read: " + lines.size());
      try {
         file.close();
      } catch (IOException e) {
      }
   }
   
   void buildCharMap(String fileName) {
      RandomAccessFile file = null;
      int len = 0;
      byte[] fileBuf = new byte[16750];
      try {
         file = new RandomAccessFile(fileName, "r");
      } catch (IOException e) {
         System.err.println("Unable to open file for reading: " + e.getMessage());
         System.exit(1);
      }
      try {
         len = file.read(fileBuf);
      } catch (IOException e) {
         System.err.println("Unable to read from file: " + e.getMessage());
      }
      int idx = 0;
      while (idx < len) {
         String part1 = "";
         String prev = "";
         ArrayList part2 = new ArrayList();
         while (fileBuf[idx] != '=') {
            part1 += (char)(0xFF & fileBuf[idx++]);
         }
         idx++;
         while (idx < len && fileBuf[idx] != 0x0D) {
            prev += (char)(0xFF & fileBuf[idx]);
            part2.add(new Byte(fileBuf[idx++]));
         }
         idx += 2;
         String chr = part1;
         ArrayList code = new ArrayList();
         while (chr.length() > 0) {
            int bval = Integer.parseInt(chr.substring(0,2),16);
            if (bval > 127) bval -= 256;
            code.add(new Byte((byte)bval));
            chr = chr.substring(2);
         }
         if (prev.equals("$")) {
            part2.clear();
            part2.add(new Byte((byte)0x0A));
         }
         charMap.put(code, part2);
      }
      try {
         file.close();
      } catch (IOException e) {
      }
   }
   
   public void writeProtectedZones(String fileName) {
      protectedZones.writeToFile(fileName);
   }
   
   private class DataFlag {
      private boolean isData;
      DataFlag(boolean val) {
         isData = val;
      }
      protected void setData(boolean val) {
         isData = val;
      }
      protected boolean isData() {
         return isData;
      }
   }
}
