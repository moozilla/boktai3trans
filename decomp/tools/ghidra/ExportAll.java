// Export functions (TSV) and decompiler output for every function in ROM.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.lang.*;
import java.io.*;
import java.math.BigInteger;

public class ExportAll extends GhidraScript {
    public void run() throws Exception {
        String out = getScriptArgs()[0];
        new File(out).mkdirs();
        PrintWriter tsv = new PrintWriter(new FileWriter(out + "/functions.tsv"));
        PrintWriter c = new PrintWriter(new FileWriter(out + "/decomp.c"));
        tsv.println("addr\tname\tmode\tsize\tcallers\tcallees");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        Register tmode = currentProgram.getProgramContext().getRegister("TMode");
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        int n = 0;
        while (it.hasNext() && !monitor.isCancelled()) {
            Function f = it.next();
            long a = f.getEntryPoint().getOffset();
            if (a < 0x08000000L || a >= 0x09000000L) continue;
            BigInteger t = currentProgram.getProgramContext().getValue(tmode, f.getEntryPoint(), false);
            String mode = (t != null && t.intValue() == 1) ? "thumb" : "arm";
            int callers = f.getCallingFunctions(monitor).size();
            int callees = f.getCalledFunctions(monitor).size();
            tsv.printf("%08X\t%s\t%s\t%d\t%d\t%d%n", a, f.getName(), mode, f.getBody().getNumAddresses(), callers, callees);
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            c.printf("// ===== %08X %s (%s) =====%n", a, f.getName(), mode);
            if (r != null && r.decompileCompleted()) c.println(r.getDecompiledFunction().getC());
            else c.println("// decompile failed");
            if (++n % 500 == 0) println("exported " + n);
        }
        tsv.close(); c.close();
        println("total functions: " + n);
    }
}
