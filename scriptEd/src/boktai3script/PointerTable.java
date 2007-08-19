package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;

public class PointerTable {
   private class TableEntry {
      private int offset;
      public TableEntry(int o) {
         offset = o;
      }
      public int getOffset() {
         return offset;
      }
      public void setOffset(int val) {
         offset = val;
      }
   }
   ArrayList offsets;
   int ctr;
   
   public PointerTable() {
      offsets = new ArrayList();
      ctr = 0;
   }
   
   public void addEntry(int o, boolean j) {
      if (j) {
         //System.out.println("Adding a data line at #" + ctr);
         offsets.add(new String("DATA"));
      } else {
         //System.out.println("Adding line #" + ctr + " at offset " + o);
         offsets.add(new TableEntry(o));
      }
      ctr++;
   }
   
   public void writeToFile(RandomAccessFile file, int offset) {
      int len = offsets.size();
      try {
         file.seek(0xD6B1F8);
      } catch (IOException e) {
         System.err.println("Unable to seek in file: " + e.getMessage());
         System.exit(1);
      }
      TableEntry entry = null;
      int off;
      int lineCtr = 0;
      ListIterator iter = offsets.listIterator();
      while (iter.hasNext()) {
         Object tmp = iter.next();
         if (tmp instanceof TableEntry) {
            entry = (TableEntry) tmp;
            off = entry.getOffset();
            off = flipBits(off);
            off |= 0x80;
            try {
               file.writeInt(off);
            } catch (IOException e) {
               System.err.println("Unable to write to file: " + e.getMessage());
               System.exit(1);
            }
         } else {
            try {
               file.skipBytes(4);
            } catch (IOException e) {
               System.err.println("Unable to write to file: " + e.getMessage());
               System.exit(1);
            }
         }
         lineCtr++;
      }
   }
   
   private int flipBits(int a) {
      int b = 0;
      b += (a & 0xFF000000) >>> 24;
      b += (a & 0x00FF0000) >>> 8;
      b += (a & 0x0000FF00) << 8;
      b += (a & 0x000000FF) << 24;
      return b;
   }
}
