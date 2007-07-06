package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;

public class PointerTable {
   ArrayList offsets;
   
   public PointerTable() {
      offsets = new ArrayList();
   }
   
   public void addEntry(int o) {
      offsets.add(new Integer(o));
   }
   
   public void writeToFile(RandomAccessFile file, int offset) {
      int len = offsets.size();
      try {
         file.seek(0xD6B1F8);
      } catch (IOException e) {
         System.err.println("Unable to seek in file: " + e.getMessage());
         System.exit(1);
      }
      int off;
      ListIterator iter = offsets.listIterator();
      while (iter.hasNext()) {
         off = ((Integer) iter.next()).intValue();
         off = flipBits(off);
         off |= 0x80;
         try {
            file.writeInt(off);
         } catch (IOException e) {
            System.err.println("Unable to write to file: " + e.getMessage());
            System.exit(1);
         }
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
