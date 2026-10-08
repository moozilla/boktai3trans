// Pre-script: create GBA memory map and seed entry points
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.lang.*;
import ghidra.program.model.symbol.*;
import java.math.BigInteger;

public class GBASetup extends GhidraScript {
    void blk(String name, long start, long len, boolean x) throws Exception {
        Memory m = currentProgram.getMemory();
        MemoryBlock b = m.createUninitializedBlock(name, toAddr(start), len, false);
        b.setRead(true); b.setWrite(true); b.setExecute(x); b.setVolatile(name.equals("IO"));
    }
    public void run() throws Exception {
        Memory m = currentProgram.getMemory();
        MemoryBlock rom = m.getBlock(toAddr(0x08000000L));
        rom.setName("ROM"); rom.setWrite(false); rom.setExecute(true);
        blk("BIOS", 0x00000000L, 0x4000, true);
        blk("EWRAM", 0x02000000L, 0x40000, true);
        blk("IWRAM", 0x03000000L, 0x8000, true);
        blk("IO", 0x04000000L, 0x400, false);
        blk("PAL", 0x05000000L, 0x400, false);
        blk("VRAM", 0x06000000L, 0x18000, false);
        blk("OAM", 0x07000000L, 0x400, false);
        blk("SRAM", 0x0E000000L, 0x10000, false);
        // ROM entry is ARM
        Register tmode = currentProgram.getProgramContext().getRegister("TMode");
        currentProgram.getProgramContext().setValue(tmode, toAddr(0x08000000L), toAddr(0x08000003L), BigInteger.ZERO);
        createFunction(toAddr(0x08000000L), "rom_entry");
        addEntryPoint(toAddr(0x08000000L));
        // Header is data
        clearListing(toAddr(0x08000004L), toAddr(0x080000BFL));
    }
}
