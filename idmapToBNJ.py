from binaryninja import *
import struct
import re

def DemangleNamings(mangledNames):
    if not mangledNames.startswith('_ZN'):
        return mangledNames
    
    try:
        remaining = mangledNames[3:]
        parts = []
        
        while remaining:
            match = re.match(r'^(\d+)([^\d].*)', remaining)
            if not match:
                break
                
            length = int(match.group(1))
            Namegroup = match.group(2)[:length]
            parts.append(Namegroup)
            remaining = match.group(2)[length:]
            
            if remaining.startswith('E'):
                break
                
        if len(parts) >= 2:
            return f"{parts[0]}::{''.join(parts[1:])}"
        return mangledNames
    except:
        return mangledNames

def IDATOBNJ(bv):
    FP = get_open_filename_input("Select .idmap file", "*.idmap")
    if FP is None:
        return
    
    try:
        with open(FP, 'rb') as f:
            while True:
                offset_bytes = f.read(4)
                if len(offset_bytes) < 4:
                    break
                offset = struct.unpack('<I', offset_bytes)[0]
                
                NameByteLength = f.read(2)
                if len(NameByteLength) < 2:
                    break
                NameLength = struct.unpack('<H', NameByteLength)[0]
                
                NameBytes = f.read(NameLength)
                if len(NameBytes) < NameLength:
                    break
                name = NameBytes.decode('utf-8')
                
                DemangledNames = DemangleNamings(name)
                
                address = bv.start + offset
                symbol = Symbol(SymbolType.FunctionSymbol, address, DemangledNames)
                bv.define_user_symbol(symbol)
                log_info(f"[IDA->BNJ] Set address name 0x{address:x} to {DemangledNames}")
    except Exception as e:
        log_error(f"[IDA->BNJ] Error importing names: {e}")

PluginCommand.register("Import idmap", "Import names of functions from .idmap file", IDATOBNJ)
