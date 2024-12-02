
module d_latch (
    input wire d,
    input wire clk,
    output reg q
);

    always_latch begin
        if (clk) begin
            q = d;
        end
    end
endmodule