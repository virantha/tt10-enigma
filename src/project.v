/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none
//`include "am_top.v"

module tt_um_virantha_enigma (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // All output pins must be assigned. If not used, assign to 0.
  //assign uo_out  = ui_in + uio_in;  // Example: ou_out is the sum of ui_in and uio_in
  assign uio_out = 0;
  assign uio_oe  = 0;

  reg [7:0] cnt;

  always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        cnt <= 0;
    end
    else begin 
        cnt <= cnt+1;
    end
  end

  assign uo_out[7:6] = cnt[7:6];

  top enigma (
    .ui_in (ui_in),
    .uo_out (uo_out[5:0]),
    .clk (clk),
    .rst (~rst_n)
  );
  /*
  Rotor r0 ( .right (ui_in[4:0]),
             .left  (uo_out[4:0])
    );
  */
  // List all unused inputs to prevent warnings
  wire _unused = ena;
  //wire _unused = &{ena, clk, rst_n, 1'b0};

endmodule
