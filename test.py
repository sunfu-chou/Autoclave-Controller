import bisect

class LUT:
    def __init__(self) -> None:
        self.bp = []
        self.table = []

    def find(self, input: float) -> float:
        if len(self.bp) and len(self.table):
            if input < self.bp[0]:
                return 0
            if input > self.bp[-1]:
                return self.table[-1]

            idx = bisect.bisect_left(self.bp, input)
            output = self.table[idx - 1] + (self.table[idx] - self.table[idx - 1]) * (input - self.bp[idx - 1]) / (
                self.bp[idx] - self.bp[idx - 1]
            )
            return output
        return -1
    
lut = LUT()
lut.bp = [
            0.4782,
            0.6701,
            1.045,
            1.6158,
            2.3332,
            3.4363,
            3.8378,
            4.3367,
            6.4171,
            9.4081,
        ]
lut.table = [
    -1.7934,
    -2.2213,
    -2.6226,
    -3.2101,
    -3.78,
    -4.4052,
    -4.5385,
    -4.7455,
    -5.4985,
    -6.2973,
]
    
print(lut.find(0))