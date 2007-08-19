/*
 * ProtectedZones.java
 *
 * Created on August 19, 2007, 5:09 AM
 */

package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;

/**
 *
 * @author Stephen
 */
public class ProtectedZones {
   
   private class ProtectedZone {
      protected int number;
      protected int start;
      protected int end;
      
      protected ProtectedZone(int n, int s, int e) {
         number = n;
         start = s;
         end = e;
      }
   }
   
   private ArrayList protectedZones;
   private ListIterator iter;
   int start;
   int end;
   
   /** Creates a new instance of ProtectedZones */
   public ProtectedZones () {
      protectedZones = new ArrayList();
      clear();
   }
   
   public void clear() {
      protectedZones.clear();
      iter = null;
      start = Integer.MAX_VALUE;
      end = start;
   }
   
   public void addZone(int n, int s, int e) {
      protectedZones.add(new ProtectedZone(n, s, e));
   }
   
   public void next() {
      if (iter != null && iter.hasNext()) {
         ProtectedZone pz = (ProtectedZone) iter.next();
         start = pz.start;
         end = pz.end;
      } else {
         start = Integer.MAX_VALUE;
         end = start;
      }
   }
   
   public void writeToFile(String fileName) {
      PrintWriter file = null;
      int len = protectedZones.size();
      try {
         file = new PrintWriter(new FileWriter(fileName));
      } catch (IOException e) {
         System.err.println("Unable to open file for writing: " + e.getMessage());
         System.exit(1);
      }
      ProtectedZone pz;
      int idx = 0;
      ListIterator iter = protectedZones.listIterator();
      while (iter.hasNext()) {
         pz = (ProtectedZone) iter.next();
         file.println(pz.number + " " + pz.start + " " + pz.end);
      }
      file.close();
   }
   
   public void readFromFile(String fileName) {
      clear();
      BufferedReader file = null;
      try {
         file = new BufferedReader(new FileReader(fileName));
      } catch (IOException e) {
         System.err.println("Unable to open file for reading: " + e.getMessage());
         System.exit(1);
      }
      String line;
      try {
         while ((line = file.readLine()) != null) {
            String[] vals = line.split("\\s");
            if (vals.length != 3) {
               continue;
            }
            addZone(Integer.parseInt(vals[0]), Integer.parseInt(vals[1]), Integer.parseInt(vals[2]));
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
   
   public int nextValidOffset(int a, int z) {
      if (iter == null) {
         iter = protectedZones.listIterator();
         next();
      }
      int len = z - a;
      len = z - a;
      while (true) {
         if (a < start && z < start) {
            return a;
         } else if (a > end && z > end) {
            next();
         } else {
            a = end + 1;
            z = a + len;
         }
      }
   }
}
