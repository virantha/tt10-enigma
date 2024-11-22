from src.rotor import Rotor_I
from amaranth.sim import Simulator

dut = Rotor_I()

async def bench(ctx):
    ctx.set(dut.en, 1)
    ctx.set(dut.load_start, 1)
    ctx.set(dut.inc, 0)
    ctx.set(dut.right_in, 0) # Load in start position

    await ctx.tick()

    # Load ring setting
    ctx.set(dut.load_start, 0)
    ctx.set(dut.right_in, 0) # Load in start position
    ctx.set(dut.load_ring, 1)
    
    await ctx.tick()

    ctx.set(dut.load_ring, 0)
    ctx.set(dut.inc, 1)
    ctx.set(dut.right_in, 11)
    
    await ctx.tick()
    for i in range(20):
        await ctx.tick()



sim = Simulator(dut)
sim.add_clock(100e-6)
sim.add_testbench(bench)
with sim.write_vcd("rotor.vcd"):
    sim.run()
