package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;

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
      readFromFile(fileName);
   }
   
   public void addEntry(String s, int l) {
      mData.add(new Metadatum(s, l));
   }
   
   public void readFromFile(String fileName) {
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
   
   public void writeToFile(String fileName) {
      PrintWriter file = null;
      int len = mData.size();
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
}
