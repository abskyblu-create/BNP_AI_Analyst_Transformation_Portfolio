from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Valuation:
    portfolio: float = 475_000_000.0
    cash: float = 18_000_000.0
    receivables: float = 7_500_000.0
    payables: float = 20_000_000.0
    expenses: float = 5_506_507.0
    units: float = 4_000_000.0
    flow: float = 3_000_000.0
    threshold: float = 2.0
    bps: int = 20
    swing: bool = True

    def calculate(self) -> dict:
        values = (self.portfolio, self.cash, self.receivables, self.payables, self.expenses, self.units, self.flow, self.threshold, self.bps)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('All inputs must be finite numbers.')
        if min(self.portfolio, self.cash, self.receivables, self.payables, self.expenses) < 0 or self.units <= 0:
            raise ValueError('Assets and liabilities must be non-negative; units must be positive.')
        if not 0 < self.threshold <= 100 or not 0 <= self.bps <= 10000:
            raise ValueError('Invalid swing threshold or factor.')
        assets = self.portfolio + self.cash + self.receivables
        liabilities = self.payables + self.expenses
        nav = assets - liabilities
        if nav <= 0:
            raise ValueError('Net assets must be positive before a valuation can be reviewed.')
        flow_pct = abs(self.flow) / nav * 100
        triggered = self.swing and self.flow != 0 and flow_pct >= self.threshold
        price = nav / self.units
        adjusted = price * (1 + (1 if self.flow > 0 else -1) * self.bps / 10000) if triggered else price
        direction = "Upward" if triggered and self.flow > 0 else "Downward" if triggered else "None"
        return dict(
            assets=assets,
            liabilities=liabilities,
            nav=nav,
            price=price,
            adjusted=adjusted,
            distribution_price=adjusted,
            flow_pct=flow_pct,
            triggered=triggered,
            direction=direction,
        )
