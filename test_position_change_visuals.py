import unittest
import pandas as pd
from plotly import graph_objects as go
from callbacks import PositionChangeVisuals

class TestPositionChangeVisuals(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5),
            'pct_change_noncomm_long': [1, 2, 3, 4, 5],
            'pct_change_noncomm_short': [-1, -2, -3, -4, -5],
            'pct_change_comm_long': [0.5, 1.5, 2.5, 3.5, 4.5],
            'pct_change_comm_short': [-0.5, -1.5, -2.5, -3.5, -4.5]
        })
        self.config = {
            'columns': [
                ('pct_change_noncomm_long', '% Change Non-Commercials Long', 'noncomm_long'),
                ('pct_change_noncomm_short', '% Change Non-Commercials Short', 'noncomm_short'),
                ('pct_change_comm_long', '% Change Commercials Long', 'comm_long'),
                ('pct_change_comm_short', '% Change Commercials Short', 'comm_short')
            ],
            'colors': {
                'noncomm_long': 'blue',
                'noncomm_short': 'cornflowerblue',
                'comm_long': 'red',
                'comm_short': 'salmon'
            },
            'bar_width': 70000000
        }

    def test_render_bars(self):
        fig = go.Figure()
        visuals = PositionChangeVisuals(self.data, self.config)
        visuals.render_bars(fig, row=1, col=1)
        
        self.assertEqual(len(fig.data), 4)
        self.assertEqual(fig.data[0].type, 'bar')
        self.assertEqual(fig.data[0].name, '% Change Non-Commercials Long')
        self.assertEqual(fig.data[1].name, '% Change Non-Commercials Short')

    def test_empty_data(self):
        fig = go.Figure()
        visuals = PositionChangeVisuals(pd.DataFrame(), self.config)
        visuals.render_bars(fig, row=1, col=1)
        self.assertEqual(len(fig.data), 0)

if __name__ == '__main__':
    unittest.main()
