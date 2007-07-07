package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.Map;
import java.util.Set;

public class ScriptMetadata {
   private class Metadatum {
      public String status;
      public int length;
      public Metadatum(String s, int l) {
         status = s;
         length = l;
      }
   }
   
   ArrayList mData;
   
   public ScriptMetadata() {
      mData = new ArrayList();
   }
   public ScriptMetadata(String fileName) {
      mData = new ArrayList();
      restoreFromFile(fileName);
   }
   
   public void addEntry(String s, int l) {
      mData.add(new Metadatum(s, l));
   }
   
   public void restoreFromFile(String fileName) {
      mData.clear();
      BufferedReader file = null;
      try {
         file = new BufferedReader(new FileReader(fileName));
      } catch (IOException e) {
         System.err.println("Unable to open file for reading: " + e.getMessage());
         System.exit(1);
      }
      String line = null;
      try {
         while ((line = file.readLine()) != null) {
            String[] ldata = line.split("\\s");
            if (ldata.length != 2) {
               System.err.println("Invalid length");
               System.exit(1);
            }
            String s = ldata[0];
            int l = Integer.parseInt(ldata[1]);
            mData.add(new Metadatum(s, l));
         }
      } catch (IOException e) {
         System.err.println("Unable to read from file: " + e.getMessage());
         System.exit(1);
      }
      try {
         file.close();
      } catch (IOException e) {
      }
   }
   
   public void storeToFile(String fileName) {
      PrintWriter file = null;
      try {
         file = new PrintWriter(new FileOutputStream(fileName));
      } catch (IOException e) {
         System.err.println("Unable to open file for writing: " + e.getMessage());
         System.exit(1);
      }
      Metadatum datum;
      ListIterator iter = mData.listIterator();
      while (iter.hasNext()) {
         datum = (Metadatum) iter.next();
         file.println(datum.status + " " + datum.length);
      }
      file.close();
   }
   
   public void printStats() {
      HashMap codes = new HashMap();
      ListIterator iter = mData.listIterator();
      Metadatum datum;
      while (iter.hasNext()) {
         datum = (Metadatum) iter.next();
         String statCode = datum.status;
         int val = 0;
         if (codes.containsKey(statCode)) {
            val = ((Integer) codes.get(statCode)).intValue();
         }
         codes.put(statCode, new Integer(1+val));
      }
      Set entries = codes.entrySet();
      Iterator iter2 = entries.iterator();
      int transCnt = 0;
      int totalCnt = 0;
      while (iter2.hasNext()) {
         Map.Entry entry = (Map.Entry) iter2.next();
         String statCode = (String) entry.getKey();
         int count = ((Integer) entry.getValue()).intValue();
         System.out.println(statCode + ": " + count);
         if (statCode.equals("E") || statCode.equals("X")) {
            transCnt += count;
         }
         totalCnt += count;
      }
      float pctComplete = ((transCnt*100f)/totalCnt);
      int wholePct = (int) pctComplete;
      int decimalPct = (int) ((pctComplete-wholePct)*100);
      System.out.println("Translation "+wholePct+"."+decimalPct+"% complete.");
   }
}
