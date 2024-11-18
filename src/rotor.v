
module Rotor (

    input wire [4:0] right,
    output wire [4:0] left
);
    // Do a lookup table to matp the permutations
    reg[4:0] data ;
   assign left=data;
   always @(right)
   begin
        case (right)
            0: data = 4;
            1: data = 10;
            2: data = 12;
            3: data = 5;
            4: data = 11;
            5: data = 6;
            6: data = 3;
            7: data = 16;
            8: data = 21;
            9: data = 25;
            10: data = 13;
            11: data = 19;
            12: data = 14;
            13: data = 22;
            14: data = 24;
            15: data = 7;
            16: data = 23;
            17: data = 20;
            18: data = 18;
            19: data = 15;
            20: data = 0;
            21: data = 8;
            22: data = 1;
            23: data = 17;
            24: data = 2;
            25: data = 9;
            default: data=31;
        endcase
   end   

endmodule