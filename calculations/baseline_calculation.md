# Baseline heat and flow calculation

```text
Q_total = 8 * 600 = 4800 W

m_dot = Q_total / (cp * Delta_T)
      = 4800 / (4180 * 10)
      = 0.11483 kg/s

V_dot = (m_dot / rho) * 60000
      = (0.11483 / 997) * 60000
      = 6.911 L/min

V_dot_branch = 6.911 / 8
             = 0.864 L/min per cold plate

T_return = T_supply + Delta_T
         = 30 + 10
         = 40 degC
```

The equal branch flow is an ideal thermal reference, not proof of hydraulic balance.

