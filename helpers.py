from decimal import Decimal
from typing import Union

# Округление qnty до определенного размера шага
def round_step_size(quantity: Union[float, Decimal], step_size: Union[float, Decimal]) -> float:
    quantity = Decimal(str(quantity))
    return float(quantity - quantity % Decimal(str(step_size)))
