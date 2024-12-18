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
  assign uio_out[7:6] = 0;
  assign uio_oe  = 8'b1111_1111;

  //assign uo_out[7] = 0;

  top enigma (
    .ui_in (ui_in),
    .uo_out (uo_out[7:0]),
    .uio_out (uio_out[5:0]),
    .clk (clk),
    .rst (~rst_n)
  );
  
  // List all unused inputs to prevent warnings
  wire _unused = &{ena,uio_in, 1'b0};

endmodule
