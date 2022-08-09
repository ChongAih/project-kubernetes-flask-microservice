import math
from typing import Dict, Callable


class Model:
    def sum_math_cos(num: float):
        output = 0
        for i in range(10 ** 6):
            output += math.cos(i * num * math.pi)
        return output

    model_mapping: Dict[str, Callable] = {
        sum_math_cos.__name__: sum_math_cos
    }
