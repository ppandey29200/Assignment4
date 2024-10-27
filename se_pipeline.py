import m5
from m5.objects import *

# Simple Pipeline CPU Class
class SimplePipelineCPU(TimingSimpleCPU):
    def __init__(self, **kwargs):
        super(SimplePipelineCPU, self).__init__(**kwargs)
        self.fetch_stage = []
        self.decode_stage = []
        self.execute_stage = []
        self.memory_stage = []
        self.writeback_stage = []
        self.cycle_count = 0
        self.insts_executed = 0

    def fetch(self, instruction):
        self.fetch_stage.append(instruction)

    def decode(self):
        if self.fetch_stage:
            instruction = self.fetch_stage.pop(0)
            self.decode_stage.append(instruction)

    def execute(self):
        if self.decode_stage:
            instruction = self.decode_stage.pop(0)
            self.execute_stage.append(instruction)

    def memory(self):
        if self.execute_stage:
            instruction = self.execute_stage.pop(0)
            self.memory_stage.append(instruction)

    def writeback(self):
        if self.memory_stage:
            instruction = self.memory_stage.pop(0)
            self.writeback_stage.append(instruction)
            self.insts_executed += 1

    def cycle(self):
        self.writeback()
        self.memory()
        self.execute()
        self.decode()
        self.cycle_count += 1

    def run(self, instructions):
        for instruction in instructions:
            self.fetch(instruction)
            self.cycle()
        while any([self.fetch_stage, self.decode_stage, self.execute_stage, self.memory_stage, self.writeback_stage]):
            self.cycle()

    def get_stats(self):
        print(f"Instructions Executed: {self.insts_executed}")
        print(f"Cycle Count: {self.cycle_count}")
        if self.cycle_count > 0:
            print(f"Throughput: {self.insts_executed / self.cycle_count}")

# Branch Predictor Class
class BranchPredictor:
    def __init__(self):
        self.history = {}

    def predict(self, branch):
        return self.history.get(branch, True)

    def update(self, branch, taken):
        self.history[branch] = taken

# Extended CPU with Branch Prediction
class SimplePipelineWithBranchPrediction(SimplePipelineCPU):
    def __init__(self):
        super().__init__()
        self.branch_predictor = BranchPredictor()

    def execute(self):
        if self.decode_stage:
            instruction = self.decode_stage.pop(0)
            if "branch" in instruction:
                prediction = self.branch_predictor.predict(instruction)
                if prediction:
                    self.execute_stage.append(instruction)
                else:
                    self.fetch_stage = []  # Flush the pipeline on misprediction
            else:
                self.execute_stage.append(instruction)

# Superscalar Configuration
class SuperscalarPipeline(SimplePipelineCPU):
    def __init__(self, issue_width=2):
        super().__init__()
        self.issue_width = issue_width

    def cycle(self):
        for _ in range(self.issue_width):
            self.writeback()
            self.memory()
            self.execute()
            self.decode()
        self.cycle_count += 1

# My System Configuration
class MySystem(System):
    def __init__(self):
        super(MySystem, self).__init__()
        self.clk_domain = SrcClockDomain()
        self.clk_domain.clock = '1GHz'
        self.clk_domain.voltage_domain = VoltageDomain()

        self.mem_mode = 'timing'
        self.mem_ranges = [AddrRange('512MB')]

        # Instantiate the CPU
        self.cpu = SimplePipelineCPU()
        self.membus = SystemXBar()

        # Connect the CPU to the membus
        self.cpu.icache_port = self.membus.cpu_side_ports
        self.cpu.dcache_port = self.membus.cpu_side_ports

        # Create a memory controller
        self.mem_ctrl = DDR3_1600_8x8()
        self.mem_ctrl.range = self.mem_ranges[0]
        self.mem_ctrl.port = self.membus.mem_side_ports

        # Connect the system port to the membus
        self.system_port = self.membus.cpu_side_ports

def run_simulation():
    print("Entering run_simulation function")
    root = Root(full_system=False, system=MySystem())

    # Define the workload
    binary = 'tests/test-progs/hello/bin/x86/linux/hello'
    process = Process()
    process.cmd = [binary]
    root.system.cpu.workload = process
    root.system.cpu.createThreads()

    m5.instantiate()
    print("Beginning simulation!")
    exit_event = m5.simulate()
    print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause()))

    # Example usage with SimplePipelineCPU
    instructions = ["inst1", "inst2", "inst3", "inst4", "inst5"]
    pipeline = SimplePipelineCPU()
    pipeline.run(instructions)
    pipeline.get_stats()

    # Example usage with branch prediction
    instructions_bp = ["inst1", "branch1", "inst2", "inst3", "branch2", "inst4", "inst5"]
    pipeline_bp = SimplePipelineWithBranchPrediction()
    pipeline_bp.run(instructions_bp)
    pipeline_bp.get_stats()

    # Example usage with superscalar pipeline
    pipeline_ss = SuperscalarPipeline(issue_width=2)
    pipeline_ss.run(instructions)
    pipeline_ss.get_stats()

run_simulation()
