

# Changelog

## V0.1
- First version commit with everything clean
   - Antenna clean
   - DRC clean (including klayout npc.2)
   - Passes tests and gate-level netlist checks
- Features:
   - Full plugboard (need to reduce this to meet bit lengths for final submission)
   - User-selectable slots for Rotors (defaults to I, II, III right to left)
   - Rotors I, II, III (IV/V omitted to save area right now)
   - Fixed Reflector B
   - LCD decoder output module on uo_out
   - Main outputs:  
       - Ready = uio_out[5]
       - Output Char = uio_out[4:0]