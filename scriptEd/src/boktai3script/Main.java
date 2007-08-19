package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;

public class Main {
   
   public Main () {
   }
   
   public static void main (String[] args) {
      String mode = "i";
      if (mode.equals("d")) {
         ScriptDumper dumper = new ScriptDumper();
         dumper.extractFromFile("shinbok.gba");
         dumper.writeToFile("dump.sjs");
         dumper.writeProtectedZones("protected_zones.txt");
      } else if (mode.equals("i")) {
         ScriptInserter loader = new ScriptInserter();
         loader.readProtectedZones("protected_zones.txt");
         loader.compileFromFile("script.sjs");
         loader.writeToFile("shinbok-edit.gba");
         loader.printStats();
      }
   }
}
