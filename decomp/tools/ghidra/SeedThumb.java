// Post-script: seed Thumb functions at push {...,lr} sites not yet covered, in the code range
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.lang.*;
import ghidra.app.cmd.disassemble.*;
import ghidra.app.cmd.function.*;
import java.math.BigInteger;

public class SeedThumb extends GhidraScript {
    public void run() throws Exception {
        long start = 0x08000000L, end = Long.parseLong(getScriptArgs().length>0?getScriptArgs()[0]:"8260000",16);
        Listing lst = currentProgram.getListing();
        Register tmode = currentProgram.getProgramContext().getRegister("TMode");
        int made = 0;
        for (int pass = 0; pass < 3; pass++) {
            for (long a = start; a < end; a += 2) {
                Address ad = toAddr(a);
                int hw = getShort(ad) & 0xffff;
                if ((hw & 0xff00) != 0xb500) continue; // push {..., lr}
                if (lst.getInstructionContaining(ad) != null) continue;
                if (getFunctionContaining(ad) != null) continue;
                // previous halfword should end something: bx, pop pc, or zero padding, or data
                int prev = getShort(toAddr(a-2)) & 0xffff;
                boolean ok = (prev & 0xff80)==0x4700 || (prev & 0xff00)==0xbd00 || prev==0 || lst.getDataContaining(toAddr(a-2))!=null || lst.getInstructionContaining(toAddr(a-2))==null;
                if (!ok) continue;
                currentProgram.getProgramContext().setValue(tmode, ad, ad.add(1), BigInteger.ONE);
                DisassembleCommand dc = new DisassembleCommand(ad, null, true);
                dc.applyTo(currentProgram, monitor);
                if (lst.getInstructionAt(ad) != null) {
                    CreateFunctionCmd cf = new CreateFunctionCmd(ad);
                    if (cf.applyTo(currentProgram, monitor)) made++;
                }
            }
            analyzeChanges(currentProgram);
        }
        println("SeedThumb created functions: " + made);
    }
}
