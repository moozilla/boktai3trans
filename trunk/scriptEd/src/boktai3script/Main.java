package boktai3script;

import java.io.*;
import java.util.ArrayList;
import java.util.ListIterator;

public class Main {
   
   public Main () {
   }
   
   public static void main (String[] args) {
      boolean dump = false;
      if (dump) {
         ScriptDumper dumper = new ScriptDumper();
         dumper.extractFromFile("shinbok.gba");
         dumper.writeToFile("dump.sjs");
      } else {
         ScriptInserter loader = new ScriptInserter();
         loader.compileFromFile("script.sjs");
         loader.writeToFile("shinbok-edit.gba");
         loader.printStats();
      }
   }
}
