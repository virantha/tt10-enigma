
module Rotor (

    input wire [4:0] right,
    output wire [4:0] left,

    input wire en,
    input wire load,
    input wire inc,
    
    input wire clk

);
    // Do a lookup table to matp the permutations
    reg[4:0] data ;
    wire[4:0] right_ptr;
    reg[4:0] cnt;

    
    always @(posedge clk) begin
        if (en) begin
            if (load) begin
                cnt <= right;
            end
            else if (inc) begin
                cnt <= (cnt + 1)%26;
            end
        end
    end

    // Convert absolute entry (right) to relative contact point on
    // the rotor by adding its rotation (cnt).
    // "data" will then be the output of the wiring pattern based on right_ptr
    
    assign right_ptr = cnt + right;
    
    // Convert the "data" which is the contacdt point on the left side
    // of the rotor, to an absolute position by subtracting out
    // the rotation of the rotor (cnt).  Thereore, "left" will be the
    // absolute position the signal will enter the next rotor to the left.
    assign left = data - cnt;
    
    always @(right_ptr)
    begin
            case (right_ptr)
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