from src.fsm import Control, Cmd

from amaranth import Const
from amaranth.sim import Simulator

dut = Control()

async def clk(clk_ctx, cycles:int=1):
    for i in range(cycles):
        await clk_ctx.tick()
async def ready(clk_ctx):
    while(clk_ctx.get(dut.ready)==0):
        await clk_ctx.tick()

async def bench(ctx):
    
    # Set all rotors
    ctx.set(dut.is_at_turnover, 0)
    ctx.set(dut.cmd, 0)

    await clk(ctx, 2)

    await clk(ctx)

    #assert ctx.get(dut.ready)
    ctx.set(dut.cmd, Cmd.LOAD_START)
    #ctx.set
        
    # while not ctx.get(dut.ready):
        
    #     await clk(ctx)
    await clk(ctx,3)

    ctx.set(dut.cmd, Cmd.NOP)

    await clk(ctx)
    ctx.set(dut.cmd, Cmd.LOAD_RING)
    
    while ctx.get(dut.ready)==0:
        await clk(ctx,3)

    ctx.set(dut.cmd, Cmd.NOP)
    await clk(ctx,1)

    ctx.set(dut.cmd, Cmd.ENCRYPT)
    await clk(ctx,1)

    await clk(ctx, 6)

    # Pretend at turnover
    ctx.set(dut.is_at_turnover[0],1)
    await clk(ctx)

    ctx.set(dut.is_at_turnover[0],0)
    await clk(ctx, 4)

    # Pretend both at turnover
    ctx.set(dut.is_at_turnover[0],1)
    ctx.set(dut.is_at_turnover[1],1)
    await clk(ctx)

    ctx.set(dut.is_at_turnover[0],0)
    await clk(ctx)
    
    ctx.set(dut.is_at_turnover[1],0)
    await clk(ctx)

    await clk(ctx, 5)


sim = Simulator(dut)
sim.add_clock(100e-6)
sim.add_testbench(bench)
with sim.write_vcd("control.vcd"):
    sim.run()
